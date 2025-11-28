-- ============================================
-- 测试数据 SQL
-- ============================================
-- 注意：使用固定 UUID 便于测试，实际使用时建议使用 gen_random_uuid()

-- 1. 插入测试用户
INSERT INTO users (id, email, password_hash, otp_verified, created_at, updated_at) VALUES
('00000000-0000-0000-0000-000000000001', 'test@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyY5Y5Y5Y5Y5', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
('00000000-0000-0000-0000-000000000002', 'admin@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyY5Y5Y5Y5Y5', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
('00000000-0000-0000-0000-000000000003', 'trader@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyY5Y5Y5Y5Y5', FALSE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

-- 2. 插入 AI 模型配置
INSERT INTO ai_models (id, user_id, name, provider, enabled, api_key, base_url, model_name, created_at, updated_at) VALUES
('10000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000001', 'OpenAI GPT-4', 'openai', TRUE, 'sk-test-key-123456', 'https://api.openai.com/v1', 'gpt-4', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
('10000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000001', 'Claude 3.5', 'anthropic', TRUE, 'sk-ant-test-key-123456', 'https://api.anthropic.com/v1', 'claude-3-5-sonnet', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
('10000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-000000000002', 'Custom Model', 'custom', TRUE, 'custom-key-123', 'https://api.example.com/v1', 'custom-model-v1', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

-- 3. 插入交易所配置
INSERT INTO exchanges (id, user_id, name, type, enabled, api_key, secret_key, testnet, hyperliquid_wallet_addr, aster_user, aster_signer, aster_private_key, created_at, updated_at) VALUES
('20000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000001', 'Binance Test', 'cex', TRUE, 'test-api-key-123', 'test-secret-key-456', TRUE, '', '', '', '', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
('20000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000001', 'OKX Test', 'cex', TRUE, 'okx-api-key-123', 'okx-secret-key-456', TRUE, '', '', '', '', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
('20000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-000000000001', 'Hyperliquid', 'dex', TRUE, '', '', FALSE, '0x1234567890abcdef1234567890abcdef12345678', '', '', '', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

-- 4. 插入提示词模板（系统默认模板）
-- 为什么报错？
-- 原因可能如下：
-- 1. prompt_templates 的表结构中 created_at 与 updated_at 没有布尔类型字段
-- 2. 插入的第一条记录包含 8 个值：('400...1', 'default', '...', '默认提示词模板', NULL, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
--    但实际表结构只有 6 列 (id, name, content, description, created_at, updated_at)
-- 3. 其中 NULL, TRUE 是多余的内容，导致字段数量与表定义不符 (列数错误)

-- 正确写法如下（与 models/prompt_template.py, init.sql 一致，每条记录 6 列）：

INSERT INTO prompt_templates (id, name, content, description, created_at, updated_at) VALUES
('40000000-0000-0000-0000-000000000001', 'default', '你是专业的加密货币交易AI，在合约市场进行自主交易。

# 核心目标
最大化夏普比率（Sharpe Ratio）

夏普比率 = 平均收益 / 收益波动率

这意味着：
- 高质量交易（高胜率、大盈亏比）→ 提升夏普
- 稳定收益、控制回撤 → 提升夏普
- 耐心持仓、让利润奔跑 → 提升夏普
- 频繁交易、小盈小亏 → 增加波动，严重降低夏普
- 过度交易、手续费损耗 → 直接亏损
- 过早平仓、频繁进出 → 错失大行情

关键认知: 系统每3分钟扫描一次，但不意味着每次都要交易！
大多数时候应该是 `wait` 或 `hold`，只在极佳机会时才开仓。', '默认提示词模板', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
('40000000-0000-0000-0000-000000000002', 'aggressive', '你是激进的加密货币交易AI，追求高收益。
# 交易策略
- 更高的杠杆使用（5-10倍）
- 更频繁的交易机会
- 更快的止盈止损
- 关注短期波动

注意：高风险高收益策略，需要严格的风险控制。', '激进交易模板', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
('40000000-0000-0000-0000-000000000003', 'conservative', '你是保守的加密货币交易AI，优先保护资本。

# 交易策略
- 低杠杆使用（2-3倍）
- 只做高确定性交易
- 长期持仓
- 严格止损

注意：稳健策略，追求长期稳定收益。', '保守交易模板', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

-- 5. 插入交易员配置
INSERT INTO traders (
    id, user_id, name, ai_model_id, exchange_id, 
    initial_balance, scan_interval_minutes, is_running,
    btc_eth_leverage, altcoin_leverage,
    trading_symbols, use_default_coins, custom_coins,
    use_coin_pool, use_oi_top, use_inside_coins,
    system_prompt_template, custom_prompt, override_base_prompt,
    is_cross_margin, decision_graph_config,
    created_at, updated_at
) VALUES
(
    '30000000-0000-0000-0000-000000000001',
    '00000000-0000-0000-0000-000000000001',
    'BTC/ETH 交易员',
    '10000000-0000-0000-0000-000000000001',
    '20000000-0000-0000-0000-000000000001',
    10000.00000000,
    3,
    FALSE,
    5,
    3,
    'BTC/USDT,ETH/USDT',
    TRUE,
    '',
    FALSE,
    TRUE,
    TRUE,
    'default',
    '',
    FALSE,
    TRUE,
    '{"nodes": ["data_collector", "signal_analyzer", "ai_decision"], "edges": [{"from": "data_collector", "to": "signal_analyzer"}, {"from": "signal_analyzer", "to": "ai_decision"}]}'::jsonb,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
),
(
    '30000000-0000-0000-0000-000000000002',
    '00000000-0000-0000-0000-000000000001',
    '山寨币交易员',
    '10000000-0000-0000-0000-000000000002',
    '20000000-0000-0000-0000-000000000002',
    5000.00000000,
    5,
    FALSE,
    3,
    5,
    'SOL/USDT,BNB/USDT,AVAX/USDT',
    FALSE,
    '["SOL/USDT", "BNB/USDT", "AVAX/USDT"]',
    TRUE,
    FALSE,
    TRUE,
    'aggressive',
    '重点关注山寨币的突破机会',
    FALSE,
    TRUE,
    NULL,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
),
(
    '30000000-0000-0000-0000-000000000003',
    '00000000-0000-0000-0000-000000000002',
    '保守型交易员',
    '10000000-0000-0000-0000-000000000003',
    '20000000-0000-0000-0000-000000000001',
    20000.00000000,
    10,
    FALSE,
    2,
    2,
    'BTC/USDT',
    TRUE,
    '',
    FALSE,
    FALSE,
    FALSE,
    'conservative',
    '',
    FALSE,
    TRUE,
    NULL,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- 6. 插入用户信号源配置
INSERT INTO user_signal_sources (id, user_id, coin_pool_url, oi_top_url, created_at, updated_at) VALUES
('50000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000001', 'https://api.example.com/coin-pool', 'https://api.example.com/oi-top', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
('50000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000002', '', '', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

-- 7. 插入系统配置
INSERT INTO system_config (key, value, updated_at) VALUES
('default_coins', '["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT"]', CURRENT_TIMESTAMP),
('max_leverage', '10', CURRENT_TIMESTAMP),
('min_balance', '100', CURRENT_TIMESTAMP),
('trading_enabled', 'true', CURRENT_TIMESTAMP),
('api_rate_limit', '100', CURRENT_TIMESTAMP);

-- 8. 插入交易记录（示例）
INSERT INTO trade_records (
    id, trader_id, symbol, side, amount, price, leverage, 
    order_id, status, created_at, updated_at
) VALUES
(
    '60000000-0000-0000-0000-000000000001',
    '30000000-0000-0000-0000-000000000001',
    'BTC/USDT',
    'buy',
    0.10000000,
    45000.00000000,
    5,
    'binance-order-123456',
    'filled',
    CURRENT_TIMESTAMP - INTERVAL '1 hour',
    CURRENT_TIMESTAMP - INTERVAL '1 hour'
),
(
    '60000000-0000-0000-0000-000000000002',
    '30000000-0000-0000-0000-000000000001',
    'ETH/USDT',
    'sell',
    1.00000000,
    2500.00000000,
    5,
    'binance-order-123457',
    'filled',
    CURRENT_TIMESTAMP - INTERVAL '30 minutes',
    CURRENT_TIMESTAMP - INTERVAL '30 minutes'
),
(
    '60000000-0000-0000-0000-000000000003',
    '30000000-0000-0000-0000-000000000002',
    'SOL/USDT',
    'buy',
    10.00000000,
    100.00000000,
    5,
    'okx-order-123458',
    'pending',
    NULL,
    CURRENT_TIMESTAMP - INTERVAL '10 minutes'
);

-- 9. 插入决策日志（示例）
INSERT INTO decision_logs (
    id, trader_id, symbol, decision_state, decision_result, 
    reasoning, confidence, created_at, updated_at
) VALUES
(
    '70000000-0000-0000-0000-000000000001',
    '30000000-0000-0000-0000-000000000001',
    'BTC/USDT',
    '{"signal_strength": 85, "trend": "bullish", "rsi": 65, "macd": "positive", "volume": "high"}'::jsonb,
    'buy',
    'BTC突破关键阻力位，RSI显示强势，MACD金叉，成交量放大，建议做多',
    0.85,
    CURRENT_TIMESTAMP - INTERVAL '1 hour',
    CURRENT_TIMESTAMP - INTERVAL '1 hour'
),
(
    '70000000-0000-0000-0000-000000000002',
    '30000000-0000-0000-0000-000000000001',
    'ETH/USDT',
    '{"signal_strength": 70, "trend": "bearish", "rsi": 35, "macd": "negative", "volume": "medium"}'::jsonb,
    'sell',
    'ETH出现回调信号，RSI超买回落，建议止盈',
    0.70,
    CURRENT_TIMESTAMP - INTERVAL '30 minutes',
    CURRENT_TIMESTAMP - INTERVAL '30 minutes'
),
(
    '70000000-0000-0000-0000-000000000003',
    '30000000-0000-0000-0000-000000000002',
    'SOL/USDT',
    '{"signal_strength": 60, "trend": "neutral", "rsi": 50, "macd": "neutral", "volume": "low"}'::jsonb,
    'hold',
    'SOL横盘整理，信号不够强烈，建议观望',
    0.60,
    CURRENT_TIMESTAMP - INTERVAL '10 minutes',
    CURRENT_TIMESTAMP - INTERVAL '10 minutes'
);

