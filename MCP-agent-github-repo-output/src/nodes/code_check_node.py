"""
Code Check Node - Validate generated code for syntax and import errors
"""
import ast
import os
import re
from typing import Dict, Any, List, Tuple, Set
from ..utils import setup_logging, get_llm_service

logger = setup_logging()


def _check_syntax_errors(file_path: str, content: str) -> List[Dict[str, Any]]:
    """Check for syntax errors in Python code"""
    errors = []
    
    try:
        ast.parse(content)
        logger.info(f"✓ Syntax check passed for {os.path.basename(file_path)}")
    except SyntaxError as e:
        errors.append({
            "file": file_path,
            "type": "SyntaxError",
            "line": e.lineno,
            "offset": e.offset,
            "message": e.msg,
            "text": e.text.strip() if e.text else "",
            "severity": "high"
        })
        logger.error(f"✗ Syntax error in {os.path.basename(file_path)} at line {e.lineno}: {e.msg}")
    except Exception as e:
        errors.append({
            "file": file_path,
            "type": "ParseError",
            "message": str(e),
            "severity": "high"
        })
        logger.error(f"✗ Parse error in {os.path.basename(file_path)}: {e}")
    
    return errors


def _check_indentation_errors(file_path: str, content: str) -> List[Dict[str, Any]]:
    """Check for common indentation issues"""
    errors = []
    lines = content.split('\n')
    
    # Check for mixed tabs and spaces
    has_tabs = any('\t' in line for line in lines)
    has_spaces = any(line.startswith('    ') for line in lines)
    
    if has_tabs and has_spaces:
        errors.append({
            "file": file_path,
            "type": "IndentationError",
            "message": "Mixed tabs and spaces detected",
            "severity": "medium"
        })
        logger.warning(f"⚠ Mixed tabs and spaces in {os.path.basename(file_path)}")
    
    # Check for try-except indentation issues
    for i, line in enumerate(lines, 1):
        stripped = line.lstrip()
        if stripped.startswith('except ') or stripped.startswith('except:'):
            # Check if previous line has proper indentation
            if i > 1:
                prev_line = lines[i-2].lstrip()
                if not prev_line.startswith('try:') and 'try:' not in prev_line:
                    # except without matching try indentation
                    errors.append({
                        "file": file_path,
                        "type": "IndentationError",
                        "line": i,
                        "message": f"'except' statement appears to have incorrect indentation",
                        "text": line.strip(),
                        "severity": "high"
                    })
    
    return errors


def _extract_imports_from_code(content: str) -> Dict[str, Set[str]]:
    """Extract all imports from Python code"""
    imports = {}
    
    try:
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
                names = [alias.name for alias in node.names if alias.name != "*"]
                if module:
                    if module not in imports:
                        imports[module] = set()
                    imports[module].update(names)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name not in imports:
                        imports[alias.name] = set()
    except Exception as e:
        logger.warning(f"Failed to extract imports: {e}")
    
    return imports


def _scan_source_directory(source_dir: str) -> Dict[str, Dict[str, Set[str]]]:
    """Scan source directory to find all available classes and functions"""
    available_symbols = {}
    
    if not os.path.exists(source_dir):
        logger.warning(f"Source directory not found: {source_dir}")
        return available_symbols
    
    for root, dirs, files in os.walk(source_dir):
        # Skip test directories
        dirs[:] = [d for d in dirs if not d.startswith('test') and d not in ['__pycache__', '.git']]
        
        for file in files:
            if not file.endswith('.py'):
                continue
            
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, source_dir)
            
            # Convert file path to module path
            module_path = rel_path.replace(os.sep, '.').replace('.py', '')
            if module_path.endswith('.__init__'):
                module_path = module_path[:-9]
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    tree = ast.parse(content)
                
                functions = set()
                classes = set()
                
                for node in tree.body:
                    if isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
                        functions.add(node.name)
                    elif isinstance(node, ast.ClassDef) and not node.name.startswith('_'):
                        classes.add(node.name)
                
                if functions or classes:
                    available_symbols[module_path] = {
                        'functions': functions,
                        'classes': classes
                    }
            except Exception as e:
                logger.debug(f"Failed to parse {file_path}: {e}")
    
    return available_symbols


def _check_import_validity(file_path: str, content: str, source_dir: str) -> List[Dict[str, Any]]:
    """Check if imported classes/functions actually exist in source code"""
    errors = []
    
    # Extract imports from generated code
    imports = _extract_imports_from_code(content)
    
    # Scan source directory for available symbols
    available_symbols = _scan_source_directory(source_dir)
    
    logger.info(f"Checking imports in {os.path.basename(file_path)}...")
    logger.info(f"Found {len(available_symbols)} modules in source directory")
    
    # Get all source module names for quick lookup
    source_modules = set(available_symbols.keys())
    
    for module, imported_names in imports.items():
        # Only check modules that exist in source directory
        # If a module is not in available_symbols, it's a third-party library, skip it
        if module not in source_modules:
            # Also check if any source module contains this as a sub-module
            is_source_submodule = any(
                source_mod.startswith(module + '.') or module.startswith(source_mod + '.')
                for source_mod in source_modules
            )
            if not is_source_submodule:
                # Not from source, skip
                continue
        
        # Now we know it's a source module, check if it exists
        if module not in available_symbols:
            # Try to find partial matches
            possible_matches = [m for m in available_symbols.keys() if module in m or m in module]
            
            if possible_matches:
                errors.append({
                    "file": file_path,
                    "type": "ImportError",
                    "module": module,
                    "message": f"Module '{module}' not found in source. Did you mean: {', '.join(possible_matches[:3])}?",
                    "severity": "high",
                    "suggestions": possible_matches
                })
            else:
                errors.append({
                    "file": file_path,
                    "type": "ImportError",
                    "module": module,
                    "message": f"Module '{module}' not found in source code",
                    "severity": "high"
                })
            logger.warning(f"✗ Module not found: {module}")
            continue
        
        # Check if imported names exist in the module
        available = available_symbols[module]
        all_available = available['functions'] | available['classes']
        
        for name in imported_names:
            if name not in all_available:
                symbol_type = "class" if name[0].isupper() else "function"
                errors.append({
                    "file": file_path,
                    "type": "ImportError",
                    "module": module,
                    "name": name,
                    "message": f"{symbol_type.capitalize()} '{name}' does not exist in module '{module}'",
                    "severity": "high",
                    "available": list(all_available),
                    "suggestions": [s for s in all_available if name.lower() in s.lower()]
                })
                logger.warning(f"✗ {symbol_type.capitalize()} '{name}' not found in {module}")
                logger.info(f"  Available in {module}: {', '.join(sorted(list(all_available)[:10]))}")
    
    if not errors:
        logger.info(f"✓ Import validation passed for {os.path.basename(file_path)}")
    
    return errors


def _read_source_files_for_module(module_path: str, source_dir: str) -> str:
    """Read the actual source code for a module"""
    try:
        # Convert module path to file path
        file_path = os.path.join(source_dir, module_path.replace('.', os.sep) + '.py')
        
        # Also try __init__.py
        init_path = os.path.join(source_dir, module_path.replace('.', os.sep), '__init__.py')
        
        source_content = ""
        
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                source_content = f.read()
            logger.info(f"  Read source from: {os.path.basename(file_path)}")
        elif os.path.exists(init_path):
            with open(init_path, 'r', encoding='utf-8', errors='ignore') as f:
                source_content = f.read()
            logger.info(f"  Read source from: {os.path.basename(init_path)}")
        
        return source_content
    except Exception as e:
        logger.warning(f"Failed to read source for {module_path}: {e}")
        return ""


def _analyze_function_purpose(func_name: str, source_code: str, llm_service) -> str:
    """Use LLM to analyze and summarize what a function does"""
    try:
        system_prompt = """You are a Python code analyst. Analyze the given function and provide a concise 1-2 sentence summary of what it does, its parameters, and what it returns."""
        
        user_prompt = f"""Analyze this function from the source code and summarize its purpose:

Function name: {func_name}

Source code context:
{source_code}

Provide a clear, concise summary in this format:
- Purpose: [what the function does]
- Parameters: [what inputs it takes]
- Returns: [what it outputs]"""
        
        summary = llm_service.generate_text(user_prompt, system_prompt)
        return summary.strip()
    except Exception as e:
        logger.warning(f"Failed to analyze {func_name}: {e}")
        return f"Function: {func_name} (analysis unavailable)"


def _learn_from_source_and_fix(file_path: str, content: str, import_errors: List[Dict[str, Any]], 
                                source_dir: str, available_symbols: Dict[str, Dict[str, Set[str]]]) -> Tuple[str, bool]:
    """Learn from source code and fix import/usage errors intelligently"""
    try:
        llm_service = get_llm_service()
        
        # Group errors by module
        errors_by_module = {}
        for err in import_errors:
            if err.get('type') == 'ImportError':
                module = err.get('module', '')
                if module:
                    if module not in errors_by_module:
                        errors_by_module[module] = []
                    errors_by_module[module].append(err)
        
        # For each problematic module, read its source code
        source_code_context = []
        function_analyses = []  # Store function purpose analyses
        
        for module, module_errors in errors_by_module.items():
            logger.info(f"Learning from source code for module: {module}")
            print(f"   📚 Learning from source code: {module}")
            
            # Try to find the correct module in source
            source_content = _read_source_files_for_module(module, source_dir)
            
            if not source_content:
                # Try to find similar modules
                print(f"   🔍 Module not found, searching for similar modules...")
                for available_module in available_symbols.keys():
                    if module in available_module or available_module in module:
                        source_content = _read_source_files_for_module(available_module, source_dir)
                        if source_content:
                            logger.info(f"  Found similar module: {available_module}")
                            print(f"   ✓ Found similar module: {available_module}")
                            module = available_module
                            break
            
            if source_content:
                # Extract key parts: imports, functions, classes
                try:
                    tree = ast.parse(source_content)
                    
                    # Get function signatures and analyze their purpose
                    functions_info = []
                    for node in tree.body:
                        if isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
                            args = [arg.arg for arg in node.args.args]
                            func_signature = f"def {node.name}({', '.join(args)})"
                            functions_info.append(func_signature)
                            
                            # Extract function source code for analysis
                            func_source_lines = source_content.split('\n')[node.lineno-1:node.end_lineno]
                            func_source = '\n'.join(func_source_lines)
                            
                            # Analyze function purpose
                            print(f"   🔍 Analyzing function: {node.name}")
                            analysis = _analyze_function_purpose(node.name, func_source, llm_service)
                            function_analyses.append({
                                'name': node.name,
                                'signature': func_signature,
                                'analysis': analysis,
                                'docstring': ast.get_docstring(node) or "No docstring"
                            })
                            print(f"   ✓ {node.name}: {analysis[:100]}...")
                    
                    # Get class info
                    classes_info = []
                    for node in tree.body:
                        if isinstance(node, ast.ClassDef) and not node.name.startswith('_'):
                            methods = [m.name for m in node.body if isinstance(m, ast.FunctionDef)]
                            classes_info.append(f"class {node.name}: methods={methods}")
                    
                    source_code_context.append({
                        'module': module,
                        'errors': module_errors,
                        'functions': functions_info,
                        'classes': classes_info,
                        'source_snippet': source_content[:5000],  # More context
                        'function_analyses': function_analyses
                    })
                    
                    # Print what we found
                    print(f"   ✓ Found {len(functions_info)} function(s) and {len(classes_info)} class(es)")
                    if functions_info:
                        print(f"      Functions: {', '.join([f.split('(')[0].replace('def ', '') for f in functions_info[:5]])}")
                    if classes_info:
                        print(f"      Classes: {', '.join([c.split(':')[0].replace('class ', '') for c in classes_info[:5]])}")
                        
                except:
                    # If parsing fails, just use raw content
                    source_code_context.append({
                        'module': module,
                        'errors': module_errors,
                        'source_snippet': source_content[:3000]
                    })
                    print(f"   ⚠️  Could not parse module, using raw content")
        
        # Build comprehensive context for LLM
        error_analysis = []
        for ctx in source_code_context:
            module = ctx['module']
            error_analysis.append(f"\n{'='*60}")
            error_analysis.append(f"MODULE: {module}")
            error_analysis.append(f"{'='*60}")
            
            for err in ctx.get('errors', []):
                error_analysis.append(f"ERROR: {err['message']}")
                if 'name' in err:
                    error_analysis.append(f"  Trying to import: {err['name']}")
                if 'available' in err and err['available']:
                    error_analysis.append(f"  Available items: {', '.join(sorted(err['available'])[:10])}")
            
            error_analysis.append(f"\nACTUAL SOURCE CODE IMPLEMENTATION:")
            if 'functions' in ctx and ctx['functions']:
                error_analysis.append(f"Available Functions:")
                for func in ctx['functions']:
                    error_analysis.append(f"  - {func}")
            
            # Add function analyses
            if 'function_analyses' in ctx and ctx['function_analyses']:
                error_analysis.append(f"\nFUNCTION PURPOSE ANALYSIS:")
                for analysis in ctx['function_analyses']:
                    error_analysis.append(f"\n  Function: {analysis['name']}")
                    error_analysis.append(f"  Signature: {analysis['signature']}")
                    error_analysis.append(f"  Docstring: {analysis['docstring'][:200]}")
                    error_analysis.append(f"  Analysis: {analysis['analysis']}")
            
            if 'classes' in ctx and ctx['classes']:
                error_analysis.append(f"\nAvailable Classes:")
                for cls in ctx['classes']:
                    error_analysis.append(f"  - {cls}")
            
            error_analysis.append(f"\nSOURCE CODE SNIPPET:")
            error_analysis.append(ctx.get('source_snippet', ''))
        
        # Build available symbols summary
        symbols_summary = []
        for module_name, symbols in available_symbols.items():
            if symbols['functions'] or symbols['classes']:
                symbols_summary.append(f"\nModule: {module_name}")
                if symbols['functions']:
                    symbols_summary.append(f"  Functions: {', '.join(sorted(list(symbols['functions'])))}")
                if symbols['classes']:
                    symbols_summary.append(f"  Classes: {', '.join(sorted(list(symbols['classes'])))}")
        
        system_prompt = """You are an expert Python developer who creates MCP service tools from source code analysis.

RULES:
1. Import ALL available functions from source code
2. Create @mcp.tool() for EVERY public function
3. Use function analysis to write clear descriptions
4. Return format: {"success": bool, "result": any, "error": str|None}
5. Keep existing helper tools

Return ONLY the complete Python code without markdown formatting."""
        
        user_prompt = f"""Fix MCP service code based on source code analysis.

FUNCTION ANALYSIS:
{''.join(error_analysis)}

AVAILABLE SYMBOLS:
{''.join(symbols_summary)}

CURRENT CODE:
{content}

TASK:
1. Read function analysis above (purpose, parameters, returns)
2. Import ALL functions from source
3. Create @mcp.tool() for EACH function with:
   - Descriptive name and description based on analysis
   - Correct parameters from function signature
   - Try-except error handling
   - Standardized return format
4. Keep helper tools (read_readme, list_files, etc.)

Return complete corrected mcp_service.py code."""
        
        logger.info("Asking LLM to learn from source code and rewrite imports...")
        fixed_code = llm_service.generate_text(user_prompt, system_prompt)
        
        # Strip markdown code fences if present
        fixed_code = re.sub(r'^```(?:python)?\s*\n?', '', fixed_code)
        fixed_code = re.sub(r'\n?\s*```\s*$', '', fixed_code)
        fixed_code = fixed_code.strip()
        
        if fixed_code and len(fixed_code) > 50:
            logger.info(f"✓ LLM learned from source and rewrote code for {os.path.basename(file_path)}")
            return fixed_code, True
        else:
            logger.warning(f"✗ LLM rewrite failed for {os.path.basename(file_path)}")
            return content, False
            
    except Exception as e:
        logger.error(f"LLM source learning error: {e}")
        return content, False


def _fix_code_with_llm(file_path: str, content: str, errors: List[Dict[str, Any]], 
                       available_symbols: Dict[str, Dict[str, Set[str]]], 
                       source_dir: str = None) -> Tuple[str, bool]:
    """Use LLM to fix code errors - intelligently learns from source code for import errors"""
    
    # Separate import errors from other errors
    import_errors = [e for e in errors if e.get('type') == 'ImportError']
    other_errors = [e for e in errors if e.get('type') != 'ImportError']
    
    # If there are import errors and we have source_dir, use intelligent learning approach
    if import_errors and source_dir:
        return _learn_from_source_and_fix(file_path, content, import_errors, source_dir, available_symbols)
    
    # Otherwise, use simple fix for syntax/indentation errors
    try:
        llm_service = get_llm_service()
        
        error_summary = "\n".join([
            f"- {err['type']} in line {err.get('line', 'N/A')}: {err['message']}"
            for err in errors
        ])
        
        # Build available symbols reference
        symbols_reference = "\n".join([
            f"Module: {module}\n  Functions: {', '.join(sorted(list(symbols['functions'])))}\n  Classes: {', '.join(sorted(list(symbols['classes'])))}"
            for module, symbols in available_symbols.items()
        ])
        
        system_prompt = """You are a Python code fixing expert. Fix the provided code based on the error report.

Requirements:
1. Fix all syntax errors and indentation issues
2. Ensure proper indentation for try-except blocks
3. Return ONLY the fixed Python code without any markdown formatting or explanations
4. Preserve the overall structure and logic of the original code"""
        
        user_prompt = f"""Fix the following Python code based on these errors:

ERRORS FOUND:
{error_summary}

AVAILABLE SYMBOLS IN SOURCE CODE:
{symbols_reference}

ORIGINAL CODE:
{content}

Please fix the code by correcting all syntax and indentation errors.

Return ONLY the fixed Python code, no markdown formatting."""
        
        fixed_code = llm_service.generate_text(user_prompt, system_prompt)
        
        # Strip markdown code fences if present
        fixed_code = re.sub(r'^```(?:python)?\s*\n?', '', fixed_code)
        fixed_code = re.sub(r'\n?\s*```\s*$', '', fixed_code)
        fixed_code = fixed_code.strip()
        
        if fixed_code and len(fixed_code) > 50:
            logger.info(f"✓ LLM successfully fixed code for {os.path.basename(file_path)}")
            return fixed_code, True
        else:
            logger.warning(f"✗ LLM fix failed for {os.path.basename(file_path)}")
            return content, False
            
    except Exception as e:
        logger.error(f"LLM code fix error: {e}")
        return content, False


def code_check_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Check generated code for syntax and import errors, fix if possible"""
    logger.info("=" * 60)
    logger.info("Starting Code Check Node")
    logger.info("=" * 60)
    
    print("\n" + "=" * 60)
    print("🔍 CODE CHECK: Validating generated code...")
    print("=" * 60)
    
    plugin = state.get("plugin", {})
    files = plugin.get("files", {})
    repo = state.get("repository", {})
    repo_root = repo.get("local_paths", {}).get("repo_root")
    source_dir = os.path.join(repo_root, "source") if repo_root else None
    
    if not source_dir or not os.path.exists(source_dir):
        logger.warning("Source directory not found, skipping import validation")
        print("⚠️  Source directory not found, skipping import validation")
        state["status"] = "running"
        return state
    
    # Scan source directory once
    available_symbols = _scan_source_directory(source_dir)
    total_symbols = sum(len(s['functions']) + len(s['classes']) for s in available_symbols.values())
    logger.info(f"Found {len(available_symbols)} modules with {total_symbols} symbols")
    print(f"📦 Scanned source: {len(available_symbols)} modules, {total_symbols} symbols")
    
    all_errors = []
    fixed_files = []
    
    # Files to check
    files_to_check = {
        "mcp_service.py": files.get("mcp_output/mcp_plugin/mcp_service.py"),
        "adapter.py": files.get("mcp_output/mcp_plugin/adapter.py"),
    }
    
    for file_name, file_path in files_to_check.items():
        if not file_path or not os.path.exists(file_path):
            logger.warning(f"File not found: {file_name}")
            continue
        
        logger.info(f"\n--- Checking {file_name} ---")
        print(f"\n📄 Checking {file_name}...")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Failed to read {file_name}: {e}")
            print(f"❌ Failed to read {file_name}: {e}")
            continue
        
        # Check 1: Syntax errors
        syntax_errors = _check_syntax_errors(file_path, content)
        
        # Check 2: Indentation errors
        indent_errors = _check_indentation_errors(file_path, content)
        
        # Check 3: Import validity
        import_errors = _check_import_validity(file_path, content, source_dir)
        
        file_errors = syntax_errors + indent_errors + import_errors
        
        if file_errors:
            print(f"\n🐛 Found {len(file_errors)} error(s) in {file_name}:")
            
            # Print each error to terminal
            for err in file_errors:
                err_type = err.get('type', 'Error')
                severity = err.get('severity', 'medium')
                message = err.get('message', 'Unknown error')
                
                severity_icon = "🔴" if severity == "high" else "🟡" if severity == "medium" else "🟢"
                print(f"  {severity_icon} {err_type}: {message}")
                
                if 'line' in err:
                    print(f"     Line {err['line']}: {err.get('text', '')}")
                if 'name' in err:
                    print(f"     Trying to import: {err['name']}")
                if 'available' in err and err['available']:
                    available_list = ', '.join(sorted(err['available'])[:5])
                    print(f"     Available: {available_list}")
            
            print()
            logger.warning(f"Found {len(file_errors)} errors in {file_name}")
            all_errors.extend(file_errors)
            
            # Try to fix with LLM
            logger.info(f"Attempting to fix {file_name} with LLM...")
            print(f"🤖 Attempting to fix with LLM...")
            
            fixed_content, success = _fix_code_with_llm(file_path, content, file_errors, available_symbols, source_dir)
            
            if success:
                # LLM successfully fixed the code, save it directly
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(fixed_content)
                    fixed_files.append(file_name)
                    logger.info(f"✓ Successfully fixed and saved {file_name}")
                    print(f"✅ Successfully fixed and saved {file_name}")
                    
                    # Verify the fix and log improvements
                    verify_syntax = _check_syntax_errors(file_path, fixed_content)
                    verify_imports = _check_import_validity(file_path, fixed_content, source_dir)
                    
                    # Log what was fixed
                    fixed_count = 0
                    if syntax_errors and len(verify_syntax) < len(syntax_errors):
                        fixed_syntax = len(syntax_errors) - len(verify_syntax)
                        logger.info(f"  ✓ Fixed {fixed_syntax} syntax error(s)")
                        print(f"   ✓ Fixed {fixed_syntax} syntax error(s)")
                        fixed_count += fixed_syntax
                    
                    if indent_errors:
                        logger.info(f"  ✓ Fixed indentation issues")
                        print(f"   ✓ Fixed indentation issues")
                    
                    if import_errors and len(verify_imports) < len(import_errors):
                        fixed_imports = len(import_errors) - len(verify_imports)
                        logger.info(f"  ✓ Fixed {fixed_imports} import error(s)")
                        print(f"   ✓ Fixed {fixed_imports} import error(s)")
                        print(f"   ✓ Learned from source code and corrected imports")
                        fixed_count += fixed_imports
                    
                    if verify_syntax:
                        logger.warning(f"  ⚠ Still has {len(verify_syntax)} syntax error(s) after fix")
                        print(f"   ⚠️  Still has {len(verify_syntax)} syntax error(s) remaining")
                    if verify_imports:
                        logger.warning(f"  ⚠ Still has {len(verify_imports)} import error(s) after fix")
                        print(f"   ⚠️  Still has {len(verify_imports)} import error(s) remaining")
                        
                except Exception as e:
                    logger.error(f"Failed to save fixed {file_name}: {e}")
                    print(f"❌ Failed to save fixed {file_name}: {e}")
            else:
                print(f"❌ LLM failed to fix {file_name}")
        else:
            logger.info(f"✓ No errors found in {file_name}")
            print(f"✅ No errors found in {file_name}")
    
    # Update state
    print("\n" + "=" * 60)
    if all_errors:
        logger.warning(f"\nTotal errors found: {len(all_errors)}")
        print(f"📊 SUMMARY: Found {len(all_errors)} total error(s)")
        
        if fixed_files:
            logger.info(f"Fixed files: {', '.join(fixed_files)}")
            print(f"✅ Fixed files: {', '.join(fixed_files)}")
            state.setdefault("code_check_fixes", []).extend(fixed_files)
        else:
            print("⚠️  No files were fixed")
        
        state.setdefault("errors", []).extend([{
            "node": "CodeCheckNode",
            "type": err["type"],
            "severity": err.get("severity", "medium"),
            "message": err["message"],
            "details": err,
            "action_taken": "attempted_fix" if fixed_files else "reported"
        } for err in all_errors])
    else:
        logger.info("\n✓ All code checks passed!")
        print("✅ All code checks passed! No errors found.")
    
    state["status"] = "running"
    state["workflow_status"] = "running"
    
    logger.info("=" * 60)
    logger.info("Code Check Node Completed")
    logger.info("=" * 60)
    print("=" * 60 + "\n")
    
    return state
