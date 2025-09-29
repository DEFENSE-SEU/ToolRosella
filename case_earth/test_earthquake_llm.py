"""
Earthquake Data Analysis with LLM and ObsPy MCP Service
Simulates LLM calling ObsPy MCP tools for seismic data processing tasks
"""

import asyncio
import json
import sys
import os
import numpy as np
from datetime import datetime, timedelta
import subprocess
import time
import httpx
from typing import List, Dict, Any

# Import OpenAI for LLM functionality
try:
    from openai import AsyncOpenAI
except ImportError:
    print("Please install OpenAI library: pip install openai")
    sys.exit(1)

# Import MCP client
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
except ImportError:
    print("Please install MCP client: pip install mcp")
    sys.exit(1)


class EarthquakeDataGenerator:
    """Generate realistic earthquake waveform and event data"""

    @staticmethod
    def generate_p_wave_arrival(duration=30, sampling_rate=100, magnitude=5.2):
        """Generate realistic P-wave arrival data based on San Francisco earthquake"""
        print(f"🌊 Generating realistic P-wave data for M{magnitude} earthquake")

        t = np.linspace(0, duration, int(duration * sampling_rate))

        # Background noise (pre-event) - typical for broadband seismometer
        noise = np.random.normal(0, 0.0005, len(t))

        # P-wave arrival parameters
        p_arrival_time = 8.5  # P-wave arrives 8.5 seconds after origin
        p_mask = t >= p_arrival_time

        # Realistic P-wave characteristics for M5.2 at 85km distance
        p_wave = np.zeros_like(t)
        if np.any(p_mask):
            # Primary P-wave: sharp onset, high frequency (5-15 Hz)
            primary_freq = 8.0
            secondary_freq = 12.0

            # Amplitude scaling based on magnitude and distance
            amplitude = (magnitude/5.0) * 0.008  # Realistic amplitude for 85km distance

            # P-wave with realistic characteristics
            time_since_arrival = t[p_mask] - p_arrival_time

            # Sharp onset with exponential decay
            envelope = amplitude * np.exp(-0.25 * time_since_arrival)

            # Multi-frequency P-wave
            p_wave[p_mask] = envelope * (
                0.7 * np.sin(2*np.pi*primary_freq*time_since_arrival) +
                0.3 * np.sin(2*np.pi*secondary_freq*time_since_arrival)
            )

            # Add realistic P-wave coda (scattered waves)
            coda_mask = time_since_arrival > 5.0
            if np.any(coda_mask):
                coda_amplitude = amplitude * 0.3
                coda_time = time_since_arrival[coda_mask]
                p_wave[p_mask][coda_mask] += coda_amplitude * \
                    np.exp(-0.1 * coda_time) * np.sin(2*np.pi*6*coda_time)

        # Combine signal with noise
        signal = noise + p_wave

        # Add some realistic instrument response characteristics
        # High-pass filter effect (removes DC)
        from scipy import signal as sp_signal
        b, a = sp_signal.butter(2, 0.5/(sampling_rate/2), btype='high')
        signal = sp_signal.filtfilt(b, a, signal)

        print(f"   📊 P-wave arrival at t={p_arrival_time}s")
        print(f"   📈 Max amplitude: {np.max(np.abs(signal)):.6f}")
        print(f"   ⏱️  Duration: {duration}s at {sampling_rate}Hz")

        return signal.tolist(), sampling_rate

    @staticmethod
    def generate_surface_wave_data(duration=180, sampling_rate=40, magnitude=6.1):
        """Generate realistic surface wave data (Love/Rayleigh waves)"""
        t = np.linspace(0, duration, int(duration * sampling_rate))

        # Background noise
        noise = np.random.normal(0, 0.0005, len(t))

        # Surface wave arrival (lower frequency, longer duration)
        surface_arrival = 45.0  # Surface waves arrive later
        surface_mask = t >= surface_arrival

        # Surface wave: lower frequency, longer duration
        surface_wave = np.zeros_like(t)
        surface_wave[surface_mask] = (magnitude/6.0) * 0.02 * \
            (np.sin(2*np.pi*0.5*(t[surface_mask]-surface_arrival)) +
             0.5*np.sin(2*np.pi*1.2*(t[surface_mask]-surface_arrival))) * \
            np.exp(-0.05*(t[surface_mask]-surface_arrival))

        signal = noise + surface_wave
        return signal.tolist(), sampling_rate

    @staticmethod
    def get_earthquake_event_data():
        """Get realistic earthquake event parameters"""
        return {
            "origin_time": "2024-03-15T14:28:33.5Z",
            "latitude": 35.7749,  # Northern California
            "longitude": -122.4194,
            "depth_km": 12.3,
            "magnitude": 5.2,
            "magnitude_type": "ML",
            "region": "San Francisco Bay Area",
            "station_distance_km": 85.2
        }


class ObsPyMCPClient:
    """Client for communicating with ObsPy MCP service"""

    def __init__(self):
        self.session = None
        self.available_tools = []

    async def connect(self):
        """Connect to ObsPy MCP service"""
        try:
            # 修正路径问题 - 使用正确的相对路径
            mcp_path = "/Users/yuanxujie/Downloads/Easy-Tool/MCP-agent-github-repo-output/workspace/obspy/mcp_output"
            
            server_params = StdioServerParameters(
                command="/Users/yuanxujie/opt/anaconda3/envs/obspy_026400_env/bin/python",
                args=["start_mcp.py"],
                cwd=mcp_path  # 修正这里的路径
            )

            self.server_params = server_params
            print("✅ ObsPy MCP client initialized")
            return True

        except Exception as e:
            print(f"❌ Failed to initialize MCP client: {e}")
            return False

    async def get_available_tools(self):
        """Get list of available MCP tools"""
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools_result = await session.list_tools()
                self.available_tools = [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": getattr(tool, 'inputSchema', {}).get('properties', {})
                    }
                    for tool in tools_result.tools
                ]
                return self.available_tools

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]):
        """Call a specific MCP tool"""
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments)
                return result


class EarthquakeLLMAgent:
    """LLM Agent for earthquake data analysis using ObsPy tools"""

    def __init__(self, api_key: str):
        self.openai_client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.gptsapi.net/v1"
        )
        self.mcp_client = ObsPyMCPClient()
        self.conversation_history = []

    async def initialize(self):
        """Initialize MCP connection and get available tools"""
        await self.mcp_client.connect()
        self.available_tools = await self.mcp_client.get_available_tools()
        print(f"📋 Available ObsPy tools: {[tool['name'] for tool in self.available_tools]}")

    def create_openai_tools_schema(self):
        """Convert MCP tools to OpenAI function calling schema"""
        openai_tools = []

        for tool in self.available_tools:
            # Create OpenAI tool schema
            openai_tool = {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }

            # Add parameters based on tool name (simplified mapping)
            if tool["name"] == "create_trace":
                openai_tool["function"]["parameters"] = {
                    "type": "object",
                    "properties": {
                        "data": {"type": "array", "items": {"type": "number"}, "description": "Seismic waveform data points"},
                        "sampling_rate": {"type": "number", "description": "Data sampling rate in Hz"}
                    },
                    "required": ["data", "sampling_rate"]
                }
            elif tool["name"] == "create_utcdatetime":
                openai_tool["function"]["parameters"] = {
                    "type": "object",
                    "properties": {
                        "timestamp": {"type": "string", "description": "ISO format timestamp"}
                    },
                    "required": ["timestamp"]
                }
            elif tool["name"] in ["create_stream", "create_catalog", "create_event"]:
                openai_tool["function"]["parameters"] = {
                    "type": "object",
                    "properties": {},
                    "required": []
                }

            openai_tools.append(openai_tool)

        return openai_tools

    async def auto_save_results(self, tool_name: str, tool_result: Any, tool_args: Dict, scenario: Dict):
        """Automatically save results after successful tool calls"""
        try:
            if not hasattr(tool_result, 'content') or not tool_result.content:
                return

            result_content = tool_result.content[0].text
            result_data = json.loads(result_content) if result_content.startswith('{') else {"raw": result_content}

            if not result_data.get('success', False):
                return

            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 修正输出目录路径 - 相对于当前脚本位置
            current_dir = os.path.dirname(os.path.abspath(__file__))
            output_dir = os.path.join(current_dir, "earthquake_analysis_results")
            os.makedirs(output_dir, exist_ok=True)


            # Auto-save based on tool type
            if tool_name == "create_trace" and "trace_stats" in result_data:
                print(f"   💾 Auto-saving waveform data...")

                filename = f"{scenario.get('data_type', 'seismic').lower().replace(' ', '_').replace('-', '_')}_trace_{timestamp}"

                # Save waveform data
                save_result = await self.mcp_client.call_tool("save_waveform_data", {
                    "trace_data": result_data,
                    "filename": filename,
                    "output_dir": output_dir
                })

                if hasattr(save_result, 'content') and save_result.content:
                    save_content = json.loads(save_result.content[0].text)
                    if save_content.get('success'):
                        print(f"   ✅ Waveform saved: {save_content.get('file_path')}")

            elif tool_name == "create_catalog":
                print(f"   💾 Auto-saving earthquake catalog...")

                # We need an event to save with catalog, so we'll save this info for later
                self.pending_catalog_data = result_data
                self.catalog_timestamp = timestamp

            elif tool_name == "create_event" and hasattr(self, 'pending_catalog_data'):
                print(f"   💾 Auto-saving earthquake catalog with event...")

                filename = f"earthquake_catalog_{self.catalog_timestamp}"

                # Save earthquake catalog
                save_result = await self.mcp_client.call_tool("save_earthquake_catalog", {
                    "catalog_info": self.pending_catalog_data,
                    "event_info": result_data,
                    "filename": filename,
                    "output_dir": output_dir
                })

                if hasattr(save_result, 'content') and save_result.content:
                    save_content = json.loads(save_result.content[0].text)
                    if save_content.get('success'):
                        print(f"   ✅ Catalog saved: {save_content.get('file_path')}")

                # Clean up
                delattr(self, 'pending_catalog_data')
                delattr(self, 'catalog_timestamp')

        except Exception as e:
            print(f"   ⚠️ Auto-save failed: {e}")

    async def generate_final_report(self, scenario: Dict, earthquake_data: Dict, analysis_result: str):
        """Generate final comprehensive analysis report"""
        try:
            print(f"\n📊 Generating comprehensive analysis report...")

            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Prepare analysis data
            analysis_data = {
                "scenario_title": scenario.get('title', 'Earthquake Analysis'),
                "data_type": scenario.get('data_type', 'Seismic'),
                "earthquake_info": earthquake_data,
                "waveform_analysis": {
                    "sampling_rate": scenario.get('sampling_rate'),
                    "data_points": len(scenario.get('waveform_data', [])),
                    "duration": len(scenario.get('waveform_data', [])) / scenario.get('sampling_rate', 1) if scenario.get('sampling_rate') else 0
                },
                "llm_analysis": analysis_result,
                "processing_timestamp": timestamp
            }

            filename = f"{scenario.get('data_type', 'earthquake').lower().replace(' ', '_')}_analysis_{timestamp}"

            # 修正输出目录路径
            current_dir = os.path.dirname(os.path.abspath(__file__))
            output_dir = os.path.join(current_dir, "earthquake_analysis_results")

            # Generate report using MCP tool
            report_result = await self.mcp_client.call_tool("generate_analysis_report", {
                "analysis_data": analysis_data,
                "filename": filename,
                "output_dir": output_dir
            })

            if hasattr(report_result, 'content') and report_result.content:
                report_content = json.loads(report_result.content[0].text)
                if report_content.get('success'):
                    files = report_content.get('files', {})
                    print(f"   ✅ Analysis report generated:")
                    print(f"      📄 JSON report: {files.get('json_report')}")
                    print(f"      📝 Text summary: {files.get('text_summary')}")
                else:
                    print(f"   ❌ Report generation failed: {report_content.get('error')}")

        except Exception as e:
            print(f"   ⚠️ Report generation failed: {e}")

#     async def process_earthquake_query(self, user_query: str, earthquake_data: Dict, scenario: Dict = None):
#         """Process earthquake analysis query using LLM and ObsPy tools"""

#         # Create system message with context
#         system_message = f"""You are an expert seismologist with access to ObsPy tools for earthquake data analysis.

# Available earthquake data:
# - Origin Time: {earthquake_data['origin_time']}
# - Location: {earthquake_data['latitude']}°N, {earthquake_data['longitude']}°W
# - Depth: {earthquake_data['depth_km']} km
# - Magnitude: {earthquake_data['magnitude']} {earthquake_data['magnitude_type']}
# - Region: {earthquake_data['region']}
# - Station Distance: {earthquake_data['station_distance_km']} km

# You have access to ObsPy MCP tools for seismic data processing. Use them appropriately to analyze the earthquake data.

# When you need to create traces with waveform data, I will provide the actual seismic data arrays.
# Focus on the seismic analysis workflow: create appropriate ObsPy objects, process the data, and provide scientific insights.

# IMPORTANT: After completing your analysis, always call the appropriate saving tools:
# - Use 'save_waveform_data' to save trace data to MiniSEED files
# - Use 'save_earthquake_catalog' to save earthquake catalogs to QuakeML files
# - Use 'generate_analysis_report' to create comprehensive analysis reports
# Always save your results to preserve the analysis for future use.
# """

#         messages = [
#             {"role": "system", "content": system_message},
#             {"role": "user", "content": user_query}
#         ]

#         openai_tools = self.create_openai_tools_schema()

#         print(f"\n🤖 LLM Processing Query: {user_query}")
#         print("=" * 60)

#         # Call LLM with function calling
#         response = await self.openai_client.chat.completions.create(
#             model="gpt-4o",
#             messages=messages,
#             tools=openai_tools,
#             tool_choice="auto",
#             temperature=0.1
#         )

#         assistant_message = response.choices[0].message
#         messages.append(assistant_message)

#         # Process tool calls
#         if assistant_message.tool_calls:
#             print(f"🔧 LLM requested {len(assistant_message.tool_calls)} tool calls")

#             for tool_call in assistant_message.tool_calls:
#                 tool_name = tool_call.function.name
#                 tool_args = json.loads(tool_call.function.arguments)

#                 print(f"\n📞 Calling tool: {tool_name}")
#                 print(f"   Arguments: {tool_args}")

#                 # Handle special case for trace creation - inject real earthquake data
#                 if tool_name == "create_trace" and "data" not in tool_args:
#                     # Use the pre-generated waveform data from scenario
#                     if hasattr(scenario, 'get') and 'waveform_data' in scenario:
#                         waveform_data = scenario['waveform_data']
#                         sampling_rate = scenario['sampling_rate']
#                         data_type = scenario['data_type']
#                     else:
#                         # Fallback to generating data
#                         if "P-wave" in user_query or "arrival" in user_query:
#                             waveform_data, sampling_rate = EarthquakeDataGenerator.generate_p_wave_arrival(
#                                 magnitude=earthquake_data['magnitude']
#                             )
#                             data_type = "P-wave"
#                         else:
#                             waveform_data, sampling_rate = EarthquakeDataGenerator.generate_surface_wave_data(
#                                 magnitude=earthquake_data['magnitude']
#                             )
#                             data_type = "Surface wave"

#                     tool_args["data"] = waveform_data[:1000]  # Use more data points
#                     tool_args["sampling_rate"] = sampling_rate

#                     print(f"   🌊 Using real {data_type} data ({len(tool_args['data'])} points at {sampling_rate}Hz)")

#                 # Call the MCP tool
#                 try:
#                     tool_result = await self.mcp_client.call_tool(tool_name, tool_args)

#                     # Parse tool result
#                     result_content = "Tool executed successfully"
#                     if hasattr(tool_result, 'content') and tool_result.content:
#                         if hasattr(tool_result.content[0], 'text'):
#                             result_content = tool_result.content[0].text

#                     print(f"   ✅ Tool result: {result_content[:100]}...")

#                     # Add tool result to conversation
#                     messages.append({
#                         "role": "tool",
#                         "tool_call_id": tool_call.id,
#                         "content": result_content
#                     })

#                     # Auto-save results after successful tool calls
#                     await self.auto_save_results(tool_name, tool_result, tool_args, scenario)

#                 except Exception as e:
#                     error_msg = f"Error calling tool {tool_name}: {str(e)}"
#                     print(f"   ❌ {error_msg}")

#                     messages.append({
#                         "role": "tool",
#                         "tool_call_id": tool_call.id,
#                         "content": error_msg
#                     })

#             # Get final response from LLM after tool execution
#             final_response = await self.openai_client.chat.completions.create(
#                 model="gpt-4o",
#                 messages=messages,
#                 temperature=0.1
#             )

#             final_answer = final_response.choices[0].message.content
#             print(f"\n🎯 LLM Final Analysis:")
#             print("=" * 60)
#             print(final_answer)

#             # Generate final comprehensive report
#             await self.generate_final_report(scenario, earthquake_data, final_answer)

#             return final_answer

#         else:
#             # No tool calls needed
#             print(f"\n💬 LLM Response (no tools used):")
#             print("=" * 60)
#             print(assistant_message.content)
#             return assistant_message.content

    async def process_earthquake_query(self, user_query: str, earthquake_data: Dict, scenario: Dict = None):
        """Process earthquake analysis query using LLM and ObsPy tools"""

        # Create system message with context
        system_message = f"""You are an expert seismologist with access to ObsPy tools for earthquake data analysis.

    Available earthquake data:
    - Origin Time: {earthquake_data['origin_time']}
    - Location: {earthquake_data['latitude']}°N, {earthquake_data['longitude']}°W
    - Depth: {earthquake_data['depth_km']} km
    - Magnitude: {earthquake_data['magnitude']} {earthquake_data['magnitude_type']}
    - Region: {earthquake_data['region']}
    - Station Distance: {earthquake_data['station_distance_km']} km

    You have access to ObsPy MCP tools for seismic data processing. Use them appropriately to analyze the earthquake data.

    When you need to create traces with waveform data, I will provide the actual seismic data arrays.
    Focus on the seismic analysis workflow: create appropriate ObsPy objects, process the data, and provide scientific insights.

    IMPORTANT: After completing your analysis, always call the appropriate saving tools:
    - Use 'save_waveform_data' to save trace data to MiniSEED files
    - Use 'save_earthquake_catalog' to save earthquake catalogs to QuakeML files
    - Use 'generate_analysis_report' to create comprehensive analysis reports
    Always save your results to preserve the analysis for future use.

    After completing all tool operations, provide a comprehensive scientific analysis in natural language that interprets the results and answers the original query.
    """

        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_query}
        ]

        openai_tools = self.create_openai_tools_schema()

        print(f"\n🤖 LLM Processing Query: {user_query}")
        print("=" * 60)

        # Call LLM with function calling
        response = await self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=openai_tools,
            tool_choice="auto",
            temperature=0.1
        )

        assistant_message = response.choices[0].message
        messages.append(assistant_message)

        # Process tool calls
        if assistant_message.tool_calls:
            print(f"🔧 LLM requested {len(assistant_message.tool_calls)} tool calls")

            for tool_call in assistant_message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                print(f"\n📞 Calling tool: {tool_name}")
                print(f"   Arguments: {tool_args}")

                # Handle special case for trace creation - inject real earthquake data
                if tool_name == "create_trace" and "data" not in tool_args:
                    # Use the pre-generated waveform data from scenario
                    if hasattr(scenario, 'get') and 'waveform_data' in scenario:
                        waveform_data = scenario['waveform_data']
                        sampling_rate = scenario['sampling_rate']
                        data_type = scenario['data_type']
                    else:
                        # Fallback to generating data
                        if "P-wave" in user_query or "arrival" in user_query:
                            waveform_data, sampling_rate = EarthquakeDataGenerator.generate_p_wave_arrival(
                                magnitude=earthquake_data['magnitude']
                            )
                            data_type = "P-wave"
                        else:
                            waveform_data, sampling_rate = EarthquakeDataGenerator.generate_surface_wave_data(
                                magnitude=earthquake_data['magnitude']
                            )
                            data_type = "Surface wave"

                    tool_args["data"] = waveform_data[:1000]  # Use more data points
                    tool_args["sampling_rate"] = sampling_rate

                    print(f"   🌊 Using real {data_type} data ({len(tool_args['data'])} points at {sampling_rate}Hz)")

                # Call the MCP tool
                try:
                    tool_result = await self.mcp_client.call_tool(tool_name, tool_args)

                    # Parse tool result
                    result_content = "Tool executed successfully"
                    if hasattr(tool_result, 'content') and tool_result.content:
                        if hasattr(tool_result.content[0], 'text'):
                            result_content = tool_result.content[0].text

                    print(f"   ✅ Tool result: {result_content[:100]}...")

                    # Add tool result to conversation
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result_content
                    })

                    # Auto-save results after successful tool calls
                    await self.auto_save_results(tool_name, tool_result, tool_args, scenario)

                except Exception as e:
                    error_msg = f"Error calling tool {tool_name}: {str(e)}"
                    print(f"   ❌ {error_msg}")

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": error_msg
                    })

            # Get final response from LLM after tool execution
            # Add explicit instruction for comprehensive analysis
            messages.append({
                "role": "user", 
                "content": """Now that you have completed the technical analysis using ObsPy tools, please provide a comprehensive scientific interpretation of the results. Your analysis should include:

    1. **Seismic Wave Characteristics**: Describe the key features observed in the waveform data (amplitude, frequency content, signal duration)
    2. **Arrival Time Analysis**: Explain the P-wave or surface wave arrival patterns and what they indicate about the earthquake source
    3. **Magnitude and Distance Effects**: Interpret how the earthquake magnitude and station distance affected the recorded signals
    4. **Geological Implications**: Discuss what the seismic data reveals about the earthquake source mechanism and regional geology
    5. **Data Quality Assessment**: Evaluate the quality of the recorded data and any limitations in the analysis
    6. **Summary and Conclusions**: Provide key findings and their significance for earthquake monitoring and research

    Please write this as a complete scientific analysis that directly answers the original query using natural language, integrating all the technical results from the ObsPy tools."""
            })

            final_response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.1
            )

            final_answer = final_response.choices[0].message.content
            print(f"\n🎯 LLM Final Scientific Analysis:")
            print("=" * 60)
            print(final_answer)

            # Generate final comprehensive report
            await self.generate_final_report(scenario, earthquake_data, final_answer)

            return final_answer

        else:
            # No tool calls needed
            print(f"\n💬 LLM Response (no tools used):")
            print("=" * 60)
            print(assistant_message.content)
            return assistant_message.content


async def run_earthquake_analysis_scenarios():
    """Run earthquake analysis scenarios"""

    # Load API key from .env
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Please set OPENAI_API_KEY in environment variables")
        return

    print("🌍 Earthquake Data Analysis with LLM + ObsPy MCP")
    print("=" * 60)

    # Initialize LLM agent
    agent = EarthquakeLLMAgent(api_key)
    await agent.initialize()

    # Get earthquake event data
    earthquake_data = EarthquakeDataGenerator.get_earthquake_event_data()

    print(f"\n📊 Earthquake Event Information:")
    print(f"   📅 Time: {earthquake_data['origin_time']}")
    print(f"   📍 Location: {earthquake_data['region']}")
    print(f"   📏 Magnitude: {earthquake_data['magnitude']} {earthquake_data['magnitude_type']}")

    # Test scenarios
    # Generate real earthquake waveform data
    p_wave_data, p_sampling_rate = EarthquakeDataGenerator.generate_p_wave_arrival(
        duration=30, sampling_rate=100, magnitude=earthquake_data['magnitude']
    )

    surface_wave_data, surface_sampling_rate = EarthquakeDataGenerator.generate_surface_wave_data(
        duration=180, sampling_rate=40, magnitude=earthquake_data['magnitude']
    )

    scenarios = [
        {
            "title": "P-wave Analysis with Real Seismic Data",
            "query": f"I have seismic data from the magnitude {earthquake_data['magnitude']} earthquake that occurred in {earthquake_data['region']} on {earthquake_data['origin_time']}. The waveform data shows clear P-wave arrivals. Please: (1) create ObsPy trace objects to analyze this P-wave data, (2) examine the signal characteristics (amplitude, frequency content, arrival time), (3) save the waveform data using save_waveform_data, and (4) generate a comprehensive analysis report. The station is located {earthquake_data['station_distance_km']} km from the epicenter.",
            "waveform_data": p_wave_data,
            "sampling_rate": p_sampling_rate,
            "data_type": "P-wave"
        },
        {
            "title": "Surface Wave Analysis and Complete Earthquake Record",
            "query": f"I need to process surface wave data from the {earthquake_data['origin_time']} earthquake in {earthquake_data['region']} (M{earthquake_data['magnitude']}). Please create a complete earthquake analysis including: (1) earthquake event catalog, (2) trace objects for surface wave analysis, (3) time processing, (4) save the earthquake catalog using save_earthquake_catalog, (5) save waveform data using save_waveform_data, and (6) generate final analysis report using generate_analysis_report. I want to understand surface wave characteristics and create a comprehensive seismic event record with all data properly saved.",
            "waveform_data": surface_wave_data,
            "sampling_rate": surface_sampling_rate,
            "data_type": "Surface wave"
        }
    ]

    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{'='*60}")
        print(f"🧪 Test Scenario {i}: {scenario['title']}")
        print(f"{'='*60}")

        try:
            result = await agent.process_earthquake_query(scenario["query"], earthquake_data, scenario)
            print(f"\n✅ Scenario {i} completed successfully")

        except Exception as e:
            print(f"\n❌ Scenario {i} failed: {e}")
            import traceback
            traceback.print_exc()

        # Wait between scenarios
        if i < len(scenarios):
            print(f"\n⏳ Waiting before next scenario...")
            await asyncio.sleep(2)

    print(f"\n🏁 All earthquake analysis scenarios completed!")


async def main():
    """Main function"""
    await run_earthquake_analysis_scenarios()


if __name__ == "__main__":
    # Check dependencies
    required_packages = ["numpy", "openai"]
    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print(f"❌ Please install missing packages: pip install {' '.join(missing_packages)}")
        sys.exit(1)

    # Run the test
    asyncio.run(main())