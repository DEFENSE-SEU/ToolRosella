#!/usr/bin/env python3
"""
测试 vaderSentiment MCP 服务的脚本
直接调用 mcp_service.py 中的函数进行测试
"""

import sys
import os

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "mcp_plugin"))

from mcp_service import analyze_sentiment, get_word_valence, get_emoji_description

def print_separator(title=""):
    """打印分隔线"""
    if title:
        print(f"\n{'='*60}")
        print(f"  {title}")
        print('='*60)
    else:
        print('-'*60)

def test_analyze_sentiment():
    """测试情感分析功能"""
    print_separator("测试功能1: analyze_sentiment - 情感分析")

    test_cases = [
        ("正面情感", "I love this product! It's absolutely amazing!"),
        ("负面情感", "This is terrible. I hate it so much."),
        ("中性情感", "The package arrived on Tuesday."),
        ("否定词", "This is not good."),
        ("感叹号强调", "This is great!!!"),
        ("全大写", "This is AWESOME!"),
        ("程度修饰词", "This is extremely good."),
        ("but转折", "The food was good but the service was terrible."),
        ("带emoji", "I love this! 😍"),
        ("网络俚语", "This movie sux!"),
        ("特殊习语", "This is the shit!"),
        ("空文本", ""),
        ("只有emoji", "😍😍😍"),
    ]

    for name, text in test_cases:
        print(f"\n测试: {name}")
        print(f"输入: \"{text}\"")
        result = analyze_sentiment(text)
        if result["success"]:
            scores = result["result"]
            print(f"结果: compound={scores['compound']:.4f}, "
                  f"pos={scores['pos']:.3f}, "
                  f"neu={scores['neu']:.3f}, "
                  f"neg={scores['neg']:.3f}")
        else:
            print(f"错误: {result['error']}")
        print_separator()

def test_get_word_valence():
    """测试单词情感值查询功能"""
    print_separator("测试功能2: get_word_valence - 查询单词情感值")

    test_words = [
        ("强正面词", "excellent"),
        ("强负面词", "terrible"),
        ("中等正面词", "good"),
        ("中等负面词", "bad"),
        ("弱正面词", "okay"),
        ("爱", "love"),
        ("恨", "hate"),
        ("程度副词", "very"),
        ("否定词", "not"),
        ("网络俚语", "sux"),
        ("中性词(不在词典)", "computer"),
        ("大小写测试", "GOOD"),
    ]

    for name, word in test_words:
        print(f"\n测试: {name}")
        print(f"查询: \"{word}\"")
        result = get_word_valence(word)
        if result["success"]:
            if result["result"]:
                valence = result["result"]["valence"]
                print(f"结果: valence={valence:.3f}")
                if valence > 2:
                    print("      → 强正面")
                elif valence > 0:
                    print("      → 正面")
                elif valence < -2:
                    print("      → 强负面")
                elif valence < 0:
                    print("      → 负面")
            else:
                print(f"结果: 未在词典中找到")
        else:
            print(f"错误: {result['error']}")
        print_separator()

def test_get_emoji_description():
    """测试emoji描述查询功能"""
    print_separator("测试功能3: get_emoji_description - 查询emoji描述")

    test_emojis = [
        ("笑脸", "😊"),
        ("爱心眼", "😍"),
        ("哭泣", "😢"),
        ("大哭", "😭"),
        ("生气", "😡"),
        ("点赞", "👍"),
        ("点踩", "👎"),
        ("红心", "❤️"),
        ("碎心", "💔"),
        ("鼓掌", "👏"),
        ("非情感emoji(汽车)", "🚗"),
        ("非情感emoji(披萨)", "🍕"),
    ]

    for name, emoji in test_emojis:
        print(f"\n测试: {name}")
        print(f"查询: \"{emoji}\"")
        result = get_emoji_description(emoji)
        if result["success"]:
            if result["result"]:
                desc = result["result"]["description"]
                print(f"结果: {desc}")
            else:
                print(f"结果: 未在emoji词典中找到")
        else:
            print(f"错误: {result['error']}")
        print_separator()

def test_comprehensive_scenario():
    """综合测试场景"""
    print_separator("综合测试: 理解情感分析结果")

    # 场景1: 分析一段文本并查询关键词
    print("\n场景1: 调试情感分析结果")
    text = "This is not bad at all!"
    print(f"文本: \"{text}\"")

    # 分析文本
    result1 = analyze_sentiment(text)
    print(f"\n情感分析结果: compound={result1['result']['compound']:.4f}")

    # 查询关键词
    result2 = get_word_valence("bad")
    print(f"词汇'bad'的分数: {result2['result']['valence']:.3f}")
    print("解释: 'not'否定了'bad'，加上感叹号强调，结果变为正面")

    print_separator()

    # 场景2: 对比不同强度的表达
    print("\n场景2: 对比不同表达方式的情感强度")
    expressions = [
        "The product is good",
        "The product is very good",
        "The product is extremely good",
        "The product is EXTREMELY GOOD!!!",
    ]

    for expr in expressions:
        result = analyze_sentiment(expr)
        print(f"{expr:40s} → compound={result['result']['compound']:.4f}")

    print_separator()

    # 场景3: emoji对情感的影响
    print("\n场景3: Emoji对情感分析的影响")

    text1 = "I love this"
    text2 = "I love this 😍"

    result1 = analyze_sentiment(text1)
    result2 = analyze_sentiment(text2)
    emoji_desc = get_emoji_description("😍")

    print(f"无emoji: \"{text1}\"")
    print(f"  → compound={result1['result']['compound']:.4f}")

    print(f"\n有emoji: \"{text2}\"")
    print(f"  → compound={result2['result']['compound']:.4f}")

    print(f"\nEmoji '😍' 的含义: {emoji_desc['result']['description']}")
    print(f"Emoji增强效果: +{result2['result']['compound'] - result1['result']['compound']:.4f}")

    print_separator()

def test_word_intensity_comparison():
    """测试词汇情感强度对比"""
    print_separator("词汇情感强度梯度对比")

    print("\n正面词汇强度递增:")
    positive_words = ["okay", "good", "great", "excellent", "outstanding"]
    for word in positive_words:
        result = get_word_valence(word)
        if result["success"] and result["result"]:
            valence = result["result"]["valence"]
            print(f"  {word:12s} → {valence:+.3f} {'█' * int(valence * 10)}")
        else:
            print(f"  {word:12s} → 未在词典中")

    print("\n负面词汇强度递增:")
    negative_words = ["bad", "poor", "awful", "terrible", "horrible"]
    for word in negative_words:
        result = get_word_valence(word)
        if result["success"] and result["result"]:
            valence = result["result"]["valence"]
            bars = '█' * int(abs(valence) * 10)
            print(f"  {word:12s} → {valence:+.3f} {bars}")
        else:
            print(f"  {word:12s} → 未在词典中")

    print_separator()

def test_real_world_examples():
    """真实案例测试"""
    print_separator("真实世界案例测试")

    examples = [
        ("亚马逊正面评论",
         "Great quality and fast shipping! The item works perfectly and exceeded my expectations. Would definitely buy again! 5 stars ⭐⭐⭐⭐⭐"),

        ("亚马逊负面评论",
         "Absolutely terrible experience. Product broke after 2 days. Customer service was rude and unhelpful. Don't waste your money! 😡"),

        ("社交媒体帖子",
         "OMG this is soooo good 😍😍😍 highly recommend!!! 👍"),

        ("混合情感评论",
         "The product itself is great and works well. However, the packaging was damaged and shipping took forever. Mixed feelings overall."),

        ("讽刺评论",
         "Yeah right, that's totally believable. Such great quality... NOT!"),
    ]

    for name, text in examples:
        print(f"\n{name}:")
        print(f"\"{text}\"")
        result = analyze_sentiment(text)
        if result["success"]:
            compound = result["result"]["compound"]
            print(f"\nCompound分数: {compound:+.4f}")
            if compound >= 0.5:
                sentiment = "强正面 😊"
            elif compound >= 0.1:
                sentiment = "正面 🙂"
            elif compound >= -0.1:
                sentiment = "中性 😐"
            elif compound >= -0.5:
                sentiment = "负面 🙁"
            else:
                sentiment = "强负面 😢"
            print(f"情感判断: {sentiment}")
            print(f"详细: pos={result['result']['pos']:.3f}, "
                  f"neu={result['result']['neu']:.3f}, "
                  f"neg={result['result']['neg']:.3f}")
        print_separator()

def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("  vaderSentiment MCP 服务测试套件")
    print("="*60)

    try:
        # 运行各项测试
        test_analyze_sentiment()
        test_get_word_valence()
        test_get_emoji_description()
        test_comprehensive_scenario()
        test_word_intensity_comparison()
        test_real_world_examples()

        print("\n" + "="*60)
        print("  所有测试完成！")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
