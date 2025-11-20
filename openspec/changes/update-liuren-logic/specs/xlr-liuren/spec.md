## ADDED Requirements

### Requirement: Taiji Point & Palace Mapping
系统 SHALL 根据用户报数 `x`,`y` 计算太极点及落宫：(x + y - 1) mod 6，对应 1-6 序列映射到大安、留连、速喜、赤口、小吉、空亡，并回填体宫(第一个数)、用宫(第二个数)。

#### Scenario: Numbers Map To LiuGong
- **WHEN** 用户输入报数 1 和 2
- **THEN** 系统计算太极点为序号 2，对应落宫“留连”，并标记体宫=1、用宫=2

### Requirement: Shichen Sequencing & YinYang Rotation
系统 SHALL 使用 XLR.md 时辰表将 `qigua_time` 映射到地支与阴阳属性，并基于阴/阳顺序输出 6 个依次轮排的地支列表（示例：亥为阴 → 酉亥丑卯巳未）。

#### Scenario: Yin Time Rolling Order
- **WHEN** 起卦时间位于 [21:00, 23:00)（亥时，阴）
- **THEN** 系统标记当前地支为亥、属性为阴，并生成 6 位地支顺序供后续落六兽/六亲使用

### Requirement: Six Beast Assignment
系统 SHALL 按文档提供的地支起始规则映射青龙/朱雀/勾陈/玄武/白虎/腾蛇（寅卯起青龙，巳午起朱雀，丑辰起勾陈，未戌起腾蛇，申酉起白虎，亥子起玄武），并与上一阶段产生的 6 个地支序列一一对应。

#### Scenario: Beast List Completes
- **WHEN** 地支序列包含酉→亥→丑→卯→巳→未
- **THEN** 系统依次得到白虎、玄武、勾陈、青龙、朱雀、腾蛇并写入排盘

### Requirement: Six Relative Derivation
系统 SHALL 以太极点对应的地支五行为基准，使用“五行相生我克”规则生成六亲：同我=兄弟、我生=子孙、生我=父母、我克=妻财、克我=官鬼，写入每个宫位。

#### Scenario: Relative Table From Base Element
- **WHEN** 太极点地支为亥（水）
- **THEN** 系统按水基准推导：水同类→兄弟，水生木→子孙，木克土→…，并输出完整六亲表

### Requirement: Knowledge Base Coverage
系统 SHALL 提供涵盖六宫、六兽、六亲、地支、五行扩展属性的知识库，内容来源于 XLR.md（含宫位含义、方向、性格、寻物提示、六兽象征、地支五行/阴阳等），供排盘与 RAG/LLM 查询。

#### Scenario: Gong Lookup Returns Rich Data
- **WHEN** 引擎查询“大安”宫
- **THEN** 知识库返回其五行、含义、方向、人体、寻物提示等属性字段

### Requirement: Yongshen LLM Prompt Contract
系统 SHALL 以约定 JSON Prompt（示例中“判断1/判断2/用神[]”结构）向 LLM 发送 `query`、六亲/六兽候选等信息，并解析返回的两条判断与最终 `用神` 列表。

#### Scenario: Model Selects Yongshen
- **WHEN** 用户问题为“我可以发财吗”
- **THEN** LLM 输出 JSON，至少包含两条判断说明与 `用神` 数组（如官鬼、妻财），供后续解释

### Requirement: Final Interpretation Prompt
系统 SHALL 在排盘、用神、知识库准备就绪后，使用文档中的“大师” Prompt 结合 `<六亲><六宫><六神>` 和 `<用神信息>`、`<query>` 生成最终解读文本与结构化摘要。

#### Scenario: Master Prompt Produces Answer
- **WHEN** 系统提供用神列表及 Query “我准备离职…”
- **THEN** LLM 根据模板返回最终解读，引用相关宫位/六亲含义并输出用户可读结果
