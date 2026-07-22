# 股票池格式说明

当前项目默认从下面这个文件读取监控股票池：

- `app/universe/stock_pool.json`

你之后如果要新增、删除、修改监控股票，通常直接编辑这个文件即可。

## 必填字段

每条股票记录至少应包含：

- `code`：股票代码，字符串
- `name`：股票名称
- `sector`：旧版主监控分类字段
- `monitor_sector`：新版主监控分类字段，可逐步替代 `sector`
- `sub_sector`：更细一级的业务方向
- `priority`：监控优先级，通常为 `1` 或 `2`

## 可选字段

- `market`：市场标签，例如 `沪A`、`深A`、`创业板`、`科创板`
- `chain_group`：产业链位置，例如 `设备`、`材料`、`气体`、`服务器`
- `pool_type`：股票池层级，例如 `core`、`extended`
- `notes`：补充说明，可为空

## 兼容说明

- 老记录可以继续使用 `sector`
- 新记录建议逐步使用 `monitor_sector`
- 当前程序会同时保留 `sector` 和 `monitor_sector` 的兼容读取
- 如果缺少 `chain_group`，系统会对已知板块补一个稳定默认值

## 推荐使用的主监控分类

编辑 `stock_pool.json` 时，建议优先使用这些 `monitor_sector` 值：

- `AI光模块/CPO`
- `AI服务器/算力硬件`
- `PCB/高速板`
- `液冷/数据中心散热`
- `半导体设备`
- `半导体材料`
- `半导体气体`
- `存储/HBM`
- `先进封装/Chiplet`

兼容旧值：

- 旧版 `半导体材料/气体` 仍可兼容读取
- 如果你新增了全新的分类名，校验器会提示你确认是否为有意新增

## 推荐使用的产业链分组

编辑 `chain_group` 时，建议优先使用以下值：

- `光模块`
- `服务器`
- `服务器/系统集成`
- `服务器/网络设备`
- `PCB`
- `PCB材料`
- `液冷`
- `设备`
- `材料`
- `气体`
- `存储`
- `封测`

## 推荐使用的市场标签

编辑 `market` 时，建议使用：

- `沪A`
- `深A`
- `创业板`
- `科创板`

## 推荐使用的股票池层级

编辑 `pool_type` 时，建议使用：

- `core`
- `extended`

## JSON 示例

```json
[
  {
    "code": "688549",
    "name": "中巨芯-U",
    "sector": "半导体气体",
    "sub_sector": "电子特气",
    "priority": 1,
    "chain_group": "气体",
    "notes": "重点观察"
  },
  {
    "code": "002371",
    "name": "北方华创",
    "monitor_sector": "半导体设备",
    "sub_sector": "设备",
    "priority": 1,
    "market": "深A",
    "chain_group": "设备",
    "pool_type": "core",
    "notes": ""
  }
]
```

## CSV 示例

如果你通过 `MONITOR_STOCK_POOL_PATH` 覆盖股票池文件，也支持 CSV：

```csv
code,name,monitor_sector,sub_sector,priority,market,chain_group,pool_type,notes
688549,中巨芯-U,半导体气体,电子特气,1,科创板,气体,core,重点观察
002371,北方华创,半导体设备,设备,1,深A,设备,core,
```

## 常见修改方式

新增股票：

1. 复制 `stock_pool.json` 里的一条现有记录
2. 修改代码、名称、主分类、细分方向、优先级
3. 如果你采用新结构，优先填写 `monitor_sector`
4. 按需补充 `market`、`chain_group`、`pool_type`
5. 检查逗号位置是否正确
6. 保存文件

删除股票：

1. 删除整条对象
2. 检查剩余 JSON 逗号是否仍然合法
3. 保存文件

修改股票：

1. 找到对应 `code`
2. 修改需要的字段
3. 保存文件

## 优先级建议

- `1`：核心重点观察股，应获得更高监控权重
- `2`：普通观察股

## 股票池层级建议

- `core`：当前主监控池
- `extended`：后续 AI 上下游扩展观察层

## 何时生效

股票池修改会在下次读取时生效，例如：

- 重新运行 `python -m app.main`
- 重新打开仪表盘
- 等待下一次定时任务运行

## 校验方式

编辑完成后，建议运行：

```bash
python -m app.main validate-stock-pool
```

当前校验会检查：

- 必填字段是否完整
- 股票代码是否重复
- 是否存在未注册的主监控分类
- 是否存在未注册的 `chain_group`
- 是否存在未注册的 `market`
- 是否存在未注册的 `pool_type`
- 源文件格式是否受支持（`.json` 或 `.csv`）
- 板块数量分布
- 产业链分组数量分布
- 优先级数量分布
- 是否存在板块过窄风险
- 是否缺少 `priority=1` 的核心股
- 是否存在板块过度集中
- 是否存在产业链分组过度集中
- 若有近似拼写错误，给出可能的修正建议

## 推荐编辑顺序

1. 编辑 `app/universe/stock_pool.json`
2. 保存文件
3. 运行 `python -m app.main validate-stock-pool`
4. 如果出现 `Unknown sectors:`，先确认是不是分类名拼写错误
5. 如果出现 `Unknown chain groups:`，先确认是不是产业链分组拼写错误
6. 如果出现 `Unknown markets:` 或 `Unknown pool types:`，先确认是不是枚举值写错了
