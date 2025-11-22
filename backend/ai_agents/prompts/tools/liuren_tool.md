# 小六壬占卜工具

## 工具名称
`perform_liuren_divination`

## 功能描述
执行小六壬起卦和解卦，返回完整的占卜结果。该工具会根据用户提供的两个数字（报数）、性别、问题类型等信息，进行起卦排盘，并提供用神分析和综合解读。

## 参数说明

### 必填参数

- **number1** (integer)
  - 描述：第一个报数
  - 范围：任意整数
  - 说明：用于确定落宫位置（算法会自动取模）

- **number2** (integer)
  - 描述：第二个报数
  - 范围：任意整数
  - 说明：用于确定时辰信息（算法会自动取模）

- **question_type** (string)
  - 描述：问题类型
  - 可选值：`事业`、`财运`、`感情`、`健康`、`考试`、`寻物`、`综合`
  - 默认值：`综合`

- **gender** (string)
  - 描述：性别
  - 可选值：`男`、`女`
  - 默认值：`男`
  - 说明：用于确定用神选择

### 可选参数

- **user_id** (integer)
  - 描述：用户 ID
  - 说明：如果提供，占卜结果会保存到数据库

## 返回格式

```json
{
  "success": true,
  "qigua": {
    "luogong": 3,
    "luogong_name": "坎宫",
    "shichen": "巳",
    "paipan_summary": "落宫为坎宫，时辰为巳时"
  },
  "jiegua": {
    "yongshen": "青龙",
    "interpretation": "青龙主文书喜事...",
    "favorable": true,
    "suggestions": ["保持冷静", "顺势而为"]
  }
}
```

## 使用示例

**输入：**
```python
{
  "number1": 3,
  "number2": 5,
  "question_type": "事业",
  "gender": "男",
  "user_id": 123
}
```

**输出：**
- 落宫：坎宫（第 3 宫）
- 用神：青龙
- 解读：青龙主文书财帛，坎宫属水主智慧...

## 注意事项

1. **数字范围**：number1 和 number2 支持任意正整数，算法会自动取模处理
2. **问题类型**：建议明确指定问题类型，以便获得更精准的解读
3. **性别影响**：性别会影响用神的选择，请准确填写
4. **数据保存**：仅当提供 user_id 时才会保存占卜记录到数据库

## 错误处理

- 参数验证失败：返回 `{"success": false, "error": "参数错误描述"}`
- 数据库错误：不影响占卜结果，仅记录日志
- 算法异常：返回友好的错误提示

## JSON Schema

```json
{
  "type": "function",
  "function": {
    "name": "perform_liuren_divination",
    "description": "执行小六壬起卦和解卦，根据两个报数（任意正整数）、性别、问题类型等信息进行占卜分析。",
    "parameters": {
      "type": "object",
      "properties": {
        "number1": {
          "type": "integer",
          "description": "第一个报数，用于确定落宫位置",
          "minimum": 1
        },
        "number2": {
          "type": "integer",
          "description": "第二个报数，用于确定时辰信息",
          "minimum": 1
        },
        "question_type": {
          "type": "string",
          "description": "问题类型",
          "enum": ["事业", "财运", "感情", "健康", "考试", "寻物", "综合"],
          "default": "综合"
        },
        "gender": {
          "type": "string",
          "description": "性别，影响用神选择",
          "enum": ["男", "女"],
          "default": "男"
        },
        "user_id": {
          "type": "integer",
          "description": "用户 ID（可选），提供后会保存占卜记录"
        }
      },
      "required": ["number1", "number2", "question_type", "gender"]
    }
  }
}
```
