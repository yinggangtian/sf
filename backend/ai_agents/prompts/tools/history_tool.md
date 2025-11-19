# 历史记录工具

## 工具名称
`get_user_history`

## 功能描述
获取用户的占卜历史统计信息，包括总占卜次数、问题类型分布、常见落宫等。用于分析用户的历史占卜模式，为解释提供更多上下文。

## 参数说明

### 必填参数

- **user_id** (integer)
  - 描述：用户 ID
  - 说明：系统会查询该用户的所有历史占卜记录

### 可选参数

- **limit** (integer)
  - 描述：返回记录数量
  - 范围：1-50
  - 默认值：10
  - 说明：限制返回的历史记录条数

- **offset** (integer)
  - 描述：分页偏移量
  - 范围：≥0
  - 默认值：0
  - 说明：用于分页查询，offset=0 表示第一页

- **question_type** (string)
  - 描述：筛选问题类型（可选）
  - 可选值：`事业`、`财运`、`感情`、`健康`、`考试`、`寻物`、`综合`
  - 说明：如果提供，只返回该类型的历史记录

## 返回格式

```json
{
  "success": true,
  "statistics": {
    "total_divinations": 15,
    "question_type_distribution": {
      "事业": 6,
      "财运": 5,
      "感情": 3,
      "综合": 1
    },
    "favorite_luogong": "坎宫",
    "last_divination_time": "2024-01-15T10:30:00Z"
  },
  "total_divinations": 15,
  "question_types": {
    "事业": 6,
    "财运": 5,
    "感情": 3
  }
}
```

## 使用示例

**输入（查询全部）：**
```python
{
  "user_id": 123,
  "limit": 10,
  "offset": 0
}
```

**输入（筛选事业类）：**
```python
{
  "user_id": 123,
  "limit": 5,
  "offset": 0,
  "question_type": "事业"
}
```

**输出：**
- 统计信息（总次数、类型分布）
- 最常见的落宫
- 最后一次占卜时间

## 分页说明

### 分页参数
- **第 1 页**：`offset=0, limit=10`
- **第 2 页**：`offset=10, limit=10`
- **第 3 页**：`offset=20, limit=10`

### 分页响应
```json
{
  "success": true,
  "statistics": {...},
  "total_divinations": 45,
  "question_types": {...}
}
```

根据 `total_divinations` 可以计算总页数。

## 历史模式分析

### 1. 频繁占卜同一问题
如果用户在短时间内多次占卜同一类型问题：
- 系统会在解释中提醒："您近期多次问卜此类问题，建议关注行动而非反复占卜"

### 2. 问题类型偏好
- **偏好事业**：可能是事业导向型用户，解释时侧重实际建议
- **偏好感情**：可能是情感敏感型用户，解释时侧重情感分析

### 3. 落宫模式
- 如果用户经常落入某些特定宫位，可能与其性格或处境有关

## 隐私保护

### 数据范围
- 仅返回统计信息，不返回完整的历史占卜内容
- 不包含用户的具体问题文本
- 不包含详细的解释内容

### 数据保留期
- 历史记录默认保留 1 年
- 用户可要求删除历史记录
- 删除后统计信息也会相应更新

## 注意事项

1. **数据时效性**：统计信息实时计算，每次占卜后自动更新
2. **降级策略**：查询失败返回空统计，不影响主流程
3. **性能优化**：统计信息已缓存，查询速度快
4. **分页限制**：单次最多返回 50 条记录

## 性能指标

- **平均响应时间**：<200ms
- **成功率**：>98%
- **缓存策略**：统计信息缓存 5 分钟

## JSON Schema

```json
{
  "type": "function",
  "function": {
    "name": "get_user_history",
    "description": "获取用户的占卜历史统计信息，包括总占卜次数、问题类型分布等。支持分页和按问题类型筛选。",
    "parameters": {
      "type": "object",
      "properties": {
        "user_id": {
          "type": "integer",
          "description": "用户 ID"
        },
        "limit": {
          "type": "integer",
          "description": "返回记录数量，默认 10，最大 50",
          "minimum": 1,
          "maximum": 50,
          "default": 10
        },
        "offset": {
          "type": "integer",
          "description": "分页偏移量，默认 0",
          "minimum": 0,
          "default": 0
        },
        "question_type": {
          "type": "string",
          "description": "筛选问题类型（可选），例如：'事业'、'财运'、'感情'",
          "enum": ["事业", "财运", "感情", "健康", "考试", "寻物", "综合"]
        }
      },
      "required": ["user_id"]
    }
  }
}
```

## 使用场景

### 1. 新用户首次占卜
- `total_divinations: 0`
- 提供新手引导和详细解释

### 2. 资深用户
- `total_divinations: >20`
- 提供更简洁的核心解读

### 3. 特定问题多次占卜
- 检测到同类型问题频繁占卜
- 提醒用户关注行动执行

## 相关工具

- **get_user_profile**：获取用户画像（包含总占卜次数）
- **perform_liuren_divination**：执行新的占卜（会更新历史记录）
