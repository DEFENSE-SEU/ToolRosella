# vaderSentiment MCP 服务测试用例

本文档包含用于测试 vaderSentiment MCP 服务的完整测试用例集。

---

## 功能1: `analyze_sentiment` - 情感分析

### 测试组1: 基础情感分析

#### 1.1 正面情感
```json
{
  "text": "I love this product! It's absolutely amazing!"
}
```
**预期结果**:
- `compound`: 接近 0.8-0.9 (强正面)
- `pos` > 0.5
- `neg`: 接近 0

---

#### 1.2 负面情感
```json
{
  "text": "This is terrible. I hate it so much."
}
```
**预期结果**:
- `compound`: 接近 -0.7 到 -0.8 (强负面)
- `neg` > 0.5
- `pos`: 接近 0

---

#### 1.3 中性情感
```json
{
  "text": "The package arrived on Tuesday."
}
```
**预期结果**:
- `compound`: 接近 0 (中性)
- `neu` > 0.8
- `pos` 和 `neg` 都很低

---

### 测试组2: 否定词处理

#### 2.1 否定词
```json
{
  "text": "This is not good."
}
```
**预期结果**:
- `compound` < 0 (负面)
- VADER 会识别 "not" 否定了 "good"

---

#### 2.2 双重否定
```json
{
  "text": "I'm not unhappy with the results."
}
```
**预期结果**:
- `compound` > 0 (偏正面)
- 双重否定应该产生正面效果

---

### 测试组3: 标点符号强调

#### 3.1 感叹号强调
```json
{
  "text": "This is great!!!"
}
```
**预期结果**:
- `compound` > "This is great" (无感叹号)
- 多个感叹号增强情感强度

---

#### 3.2 问号效果
```json
{
  "text": "Is this really good???"
}
```
**预期结果**:
- 多个问号也会增强情感

---

### 测试组4: 全大写强调

#### 4.1 全大写词汇
```json
{
  "text": "This is AWESOME!"
}
```
**预期结果**:
- `compound` > "This is awesome" (正常大小写)
- 全大写强调情感

---

#### 4.2 全句大写
```json
{
  "text": "I LOVE THIS SO MUCH"
}
```
**预期结果**:
- 比正常大小写的情感强度更高

---

### 测试组5: 程度修饰词

#### 5.1 增强词 (booster)
```json
{
  "text": "This is extremely good."
}
```
**预期结果**:
- `compound` > "This is good"
- "extremely" 增强了 "good" 的情感

---

#### 5.2 减弱词 (dampener)
```json
{
  "text": "This is kind of good."
}
```
**预期结果**:
- `compound` < "This is good"
- "kind of" 减弱了 "good" 的情感

---

### 测试组6: 对比连词 "but"

#### 6.1 but 转折
```json
{
  "text": "The food was good but the service was terrible."
}
```
**预期结果**:
- `compound` < 0 (偏负面)
- VADER 会给 "but" 后的内容更高权重

---

#### 6.2 反向转折
```json
{
  "text": "The service was terrible but the food was excellent."
}
```
**预期结果**:
- `compound` > 0 (偏正面)
- "but" 后的正面内容权重更高

---

### 测试组7: Emoji 处理

#### 7.1 正面 emoji
```json
{
  "text": "I love this! 😍"
}
```
**预期结果**:
- `compound` > "I love this!" (无 emoji)
- 😍 会增强正面情感

---

#### 7.2 负面 emoji
```json
{
  "text": "This is disappointing 😢"
}
```
**预期结果**:
- `compound` < "This is disappointing" (无 emoji)
- 😢 会增强负面情感

---

#### 7.3 混合 emoji
```json
{
  "text": "Good news 😊 but still worried 😰"
}
```
**预期结果**:
- 混合情感，compound 接近 0 或略正/负

---

### 测试组8: 俚语和网络用语

#### 8.1 网络俚语
```json
{
  "text": "This movie sux!"
}
```
**预期结果**:
- `compound` < 0
- VADER 识别 "sux" (sucks 的俚语)

---

#### 8.2 缩写和首字母词
```json
{
  "text": "lol this is hilarious"
}
```
**预期结果**:
- `compound` > 0
- "lol" 和 "hilarious" 都是正面

---

### 测试组9: 特殊习语

#### 9.1 特殊短语
```json
{
  "text": "This is the shit!"
}
```
**预期结果**:
- `compound` > 0 (正面！)
- VADER 识别 "the shit" 是俚语中的赞美

---

#### 9.2 反讽短语
```json
{
  "text": "Yeah right, that's believable."
}
```
**预期结果**:
- `compound` < 0
- "yeah right" 通常表示讽刺

---

### 测试组10: 长文本和复杂句子

#### 10.1 长评论
```json
{
  "text": "I recently purchased this product and I must say I'm extremely satisfied. The quality is outstanding, delivery was fast, and customer service was very helpful. Highly recommend!"
}
```
**预期结果**:
- `compound` > 0.7 (强正面)
- 多个正面词汇累积效果

---

#### 10.2 混合情感长文本
```json
{
  "text": "The product itself is great and works well. However, the packaging was damaged and shipping took forever. Mixed feelings overall."
}
```
**预期结果**:
- `compound` 接近 0 (混合情感)
- 正面和负面词汇相互抵消

---

### 测试组11: 边界情况

#### 11.1 空文本
```json
{
  "text": ""
}
```
**预期结果**:
- 所有分数应该为 0 或处理错误

---

#### 11.2 只有标点
```json
{
  "text": "!!! ??? ..."
}
```
**预期结果**:
- 接近中性或 0 分

---

#### 11.3 只有 emoji
```json
{
  "text": "😍😍😍"
}
```
**预期结果**:
- `compound` > 0 (正面)
- 只有 emoji 也能分析

---

## 功能2: `get_word_valence` - 查询单词情感值

### 测试组12: 常见情感词

#### 12.1 强正面词
```json
{
  "word": "excellent"
}
```
**预期结果**:
- `valence`: 约 3.0 到 3.4 (强正面)

---

#### 12.2 强负面词
```json
{
  "word": "terrible"
}
```
**预期结果**:
- `valence`: 约 -3.0 到 -3.2 (强负面)

---

#### 12.3 中等正面词
```json
{
  "word": "good"
}
```
**预期结果**:
- `valence`: 约 1.5 到 2.0

---

#### 12.4 中等负面词
```json
{
  "word": "bad"
}
```
**预期结果**:
- `valence`: 约 -2.0 到 -2.5

---

### 测试组13: 情感强度对比

#### 13.1 正面词梯度
依次查询以下词，观察情感强度递增：
```json
{"word": "okay"}      // 弱正面 ~0.9
{"word": "good"}      // 中等正面 ~1.9
{"word": "great"}     // 强正面 ~3.1
{"word": "excellent"} // 极强正面 ~3.4
```

---

#### 13.2 负面词梯度
依次查询以下词，观察情感强度递增：
```json
{"word": "bad"}       // 中等负面 ~-2.5
{"word": "awful"}     // 强负面 ~-3.0
{"word": "terrible"}  // 极强负面 ~-3.1
{"word": "horrible"}  // 极强负面 ~-3.2
```

---

### 测试组14: 特殊词汇

#### 14.1 程度副词
```json
{"word": "very"}
{"word": "extremely"}
{"word": "slightly"}
{"word": "kind"}
```
**预期结果**:
- 这些词本身可能在词典中，也可能不在（VADER 通过规则处理它们）

---

#### 14.2 否定词
```json
{"word": "not"}
{"word": "never"}
{"word": "no"}
```
**预期结果**:
- 可能返回负面值，或者 VADER 通过规则而非词典处理

---

### 测试组15: 俚语和网络用语

#### 15.1 网络俚语
```json
{"word": "sux"}
{"word": "lol"}
{"word": "omg"}
```
**预期结果**:
- 应该在 VADER 词典中

---

### 测试组16: 不在词典中的词

#### 16.1 中性名词
```json
{"word": "computer"}
{"word": "table"}
{"word": "Tuesday"}
```
**预期结果**:
- 返回 `None` 或提示未找到

---

#### 16.2 大小写测试
```json
{"word": "GOOD"}     // 应该查到 (自动转小写)
{"word": "Good"}     // 应该查到
{"word": "good"}     // 应该查到
```
**预期结果**:
- 所有变体都应返回相同的 valence (不区分大小写)

---

## 功能3: `get_emoji_description` - 查询 emoji 描述

### 测试组17: 常见正面 emoji

#### 17.1 笑脸系列
```json
{"emoji": "😊"}  // smiling face
{"emoji": "😁"}  // grinning face
{"emoji": "😍"}  // heart eyes
{"emoji": "🥰"}  // smiling face with hearts
```
**预期结果**:
- 返回对应的英文描述

---

### 测试组18: 常见负面 emoji

#### 18.1 悲伤/生气系列
```json
{"emoji": "😢"}  // crying face
{"emoji": "😭"}  // loudly crying face
{"emoji": "😡"}  // pouting face
{"emoji": "😠"}  // angry face
```
**预期结果**:
- 返回对应的英文描述

---

### 测试组19: 手势 emoji

#### 19.1 手势表情
```json
{"emoji": "👍"}  // thumbs up
{"emoji": "👎"}  // thumbs down
{"emoji": "👏"}  // clapping hands
{"emoji": "🙏"}  // folded hands
```
**预期结果**:
- 返回对应的英文描述

---

### 测试组20: 心形 emoji

#### 20.1 各种心形
```json
{"emoji": "❤️"}   // red heart
{"emoji": "💔"}  // broken heart
{"emoji": "💕"}  // two hearts
{"emoji": "💖"}  // sparkling heart
```
**预期结果**:
- 返回对应的英文描述

---

### 测试组21: 不在词典中的 emoji

#### 21.1 非情感 emoji
```json
{"emoji": "🚗"}  // car
{"emoji": "🍕"}  // pizza
{"emoji": "⚽"}  // soccer ball
```
**预期结果**:
- 返回 `None` 或提示未找到
- VADER 主要收录情感相关的 emoji

---

### 测试组22: 复合测试

#### 22.1 emoji 对情感分析的影响
**步骤**:
1. 先用 `analyze_sentiment` 分析: `"I love this"`
2. 再分析: `"I love this 😍"`
3. 用 `get_emoji_description` 查询 `"😍"`
4. 对比两次分析结果，理解 emoji 的贡献

---

#### 22.2 词汇+emoji 组合效果
**步骤**:
1. 用 `get_word_valence` 查询 `"love"` 的分数
2. 用 `get_emoji_description` 查询 `"😍"` 的描述
3. 用 `analyze_sentiment` 分析 `"love 😍"`
4. 理解词汇和 emoji 如何共同作用

---

## 综合测试场景

### 场景1: 调试情感分析结果

**目标**: 理解为什么某段文本的情感分数是特定值

1. 分析文本: `"This is not bad at all!"`
   ```json
   {"text": "This is not bad at all!"}
   ```

2. 查询关键词 "bad":
   ```json
   {"word": "bad"}
   ```

3. **理解**: "not" 否定了 "bad"，加上感叹号强调，结果应该是正面

---

### 场景2: 比较不同表达方式

**目标**: 对比不同措辞的情感强度

1. 分析: `"The product is good"`
2. 分析: `"The product is very good"`
3. 分析: `"The product is extremely good"`
4. 分析: `"The product is EXTREMELY GOOD!!!"`

**观察**: 情感强度逐步递增

---

### 场景3: 社交媒体文本分析

**目标**: 测试典型的社交媒体评论

```json
{
  "text": "OMG this is soooo good 😍😍😍 highly recommend!!! 👍"
}
```

然后分别查询:
- `{"word": "omg"}`
- `{"emoji": "😍"}`
- `{"emoji": "👍"}`

**理解**: VADER 如何处理俚语、emoji 和强调

---

### 场景4: 产品评论分析

**真实案例**: 亚马逊风格的评论

```json
{
  "text": "Great quality and fast shipping! The item works perfectly and exceeded my expectations. Customer service was also very responsive. Would definitely buy again! 5 stars ⭐⭐⭐⭐⭐"
}
```

**预期**: 强正面，compound > 0.8

---

### 场景5: 负面评论分析

**真实案例**: 投诉评论

```json
{
  "text": "Absolutely terrible experience. Product broke after 2 days. Customer service was rude and unhelpful. Don't waste your money! 😡"
}
```

**预期**: 强负面，compound < -0.7

---

## 性能测试

### 测试组23: 批量分析

依次调用 `analyze_sentiment` 分析 100 条文本，观察：
- 响应时间
- 稳定性
- 错误率

---

## 错误处理测试

### 测试组24: 异常输入

#### 24.1 非字符串输入
```json
{"text": 123}
{"text": null}
{"text": ["array"]}
```

#### 24.2 特殊字符
```json
{"text": "���乱码���"}
{"text": "<script>alert('xss')</script>"}
```

#### 24.3 超长文本
```json
{"text": "超过 10000 字的长文本..."}
```

---

## 测试执行建议

### 自动化测试脚本

建议创建一个 Python 脚本来批量运行这些测试用例，记录：
1. 每个测试的输入
2. 实际输出
3. 是否符合预期
4. 响应时间

### 手动探索测试

以下场景适合手动测试和探索：
1. 测试组 22 (复合测试) - 理解功能之间的联系
2. 场景 1-5 (综合场景) - 真实使用案例
3. 边界情况 - 发现意外行为

---

## 预期输出格式示例

### analyze_sentiment 输出
```json
{
  "success": true,
  "result": {
    "neg": 0.0,
    "neu": 0.254,
    "pos": 0.746,
    "compound": 0.8545
  },
  "error": null
}
```

### get_word_valence 输出
```json
{
  "success": true,
  "result": {
    "word": "excellent",
    "valence": 3.4
  },
  "error": null
}
```

### get_emoji_description 输出
```json
{
  "success": true,
  "result": {
    "emoji": "😍",
    "description": "smiling face with heart-shaped eyes"
  },
  "error": null
}
```
