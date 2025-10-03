# 修复总结

## 1. 修复 Hamiltonian 导入错误
- 原代码：
```python
from tencirchem.static.hamiltonian import Hamiltonian
```
- 修复后：

```python
from tencirchem.static.hamiltonian import get_h_from_hf
```
说明：TenCirChem 中没有 Hamiltonian 类，而是使用函数 get_h_from_hf 来创建哈密顿量。

## 2. 修复 Molecule 导入错误
- 原代码：

python
```
from tencirchem.molecule import Molecule
```
- 修复后：

python
```
from pyscf import M
```
说明：TenCirChem 中的 Molecule 类实际上是 _Molecule，而 UCC 类期望接收 PySCF 的 Mole 对象。

## 3. 修复 Optimizer 导入错误
原代码：

python
```
from tencirchem.utils.optimizer import Optimizer
```
修复后：
移除该导入

说明：TenCirChem 中没有 Optimizer 类，UCC 类内部已经处理了优化。

## 4. 修复 callable 类型错误
原代码使用 optimize_parameters 函数

修复后使用：

python
```
get_ucc_parameters
```
说明：FastMCP 无法处理 callable 类型作为参数，所以改为更实用的函数。

## 5. 更新所有函数以使用正确的 API
create_hamiltonian
使用 PySCF 的 M 类创建分子，然后使用 get_h_from_hf 创建哈密顿量。

run_ucc
使用 PySCF 的 M 类创建分子，然后创建 UCC 对象。

simulate_time_evolution
使用 PySCF 的 M 类创建分子，然后创建 TimeEvolution 对象。

get_ucc_parameters
新增函数，用于获取 UCC 计算后的优化参数。
