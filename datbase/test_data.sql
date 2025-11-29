-- ============================================
-- 测试数据生成脚本
-- 每个表10条测试数据
-- 注意：需要先执行表结构创建脚本
-- ============================================
--
-- 执行顺序（重要！必须按此顺序执行，否则会出现外键错误）：
-- 1. users (基础表，无依赖)
-- 2. ai_models (依赖 users)
-- 3. exchanges (依赖 users)
-- 4. prompt_templates (无依赖)
-- 5. user_signal_sources (依赖 users，且 user_id 唯一)
-- 6. traders (依赖 users, ai_models, exchanges)
-- 7. trade_records (依赖 traders)
-- 8. decision_logs (依赖 traders)
-- 9. system_config (无依赖)
--
-- ============================================

-- 1. users 表 (10条) - 基础表
INSERT INTO public.users (id, email, password_hash, otp_secret, otp_verified, created_at, updated_at) VALUES
('11111111-1111-1111-1111-111111111111', 'user1@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyY5Y5Y5Y5Yu', 'ABCDEFGHIJKLMNOP', true, '2024-01-01 10:00:00', '2024-01-01 10:00:00'),
('22222222-2222-2222-2222-222222222222', 'user2@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyY5Y5Y5Y5Yu', 'BCDEFGHIJKLMNOPQ', true, '2024-01-02 10:00:00', '2024-01-02 10:00:00'),
('33333333-3333-3333-3333-333333333333', 'user3@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyY5Y5Y5Y5Yu', 'CDEFGHIJKLMNOPQR', false, '2024-01-03 10:00:00', '2024-01-03 10:00:00'),
('44444444-4444-4444-4444-444444444444', 'user4@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyY5Y5Y5Y5Yu', 'DEFGHIJKLMNOPQRS', true, '2024-01-04 10:00:00', '2024-01-04 10:00:00'),
('55555555-5555-5555-5555-555555555555', 'user5@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyY5Y5Y5Y5Yu', 'EFGHIJKLMNOPQRST', false, '2024-01-05 10:00:00', '2024-01-05 10:00:00'),
('66666666-6666-6666-6666-666666666666', 'user6@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyY5Y5Y5Y5Yu', 'FGHIJKLMNOPQRSTU', true, '2024-01-06 10:00:00', '2024-01-06 10:00:00'),
('77777777-7777-7777-7777-777777777777', 'user7@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyY5Y5Y5Y5Yu', 'GHIJKLMNOPQRSTUV', true, '2024-01-07 10:00:00', '2024-01-07 10:00:00'),
('88888888-8888-8888-8888-888888888888', 'user8@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyY5Y5Y5Y5Yu', 'HIJKLMNOPQRSTUVW', false, '2024-01-08 10:00:00', '2024-01-08 10:00:00'),
('99999999-9999-9999-9999-999999999999', 'user9@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyY5Y5Y5Y5Yu', 'IJKLMNOPQRSTUVWX', true, '2024-01-09 10:00:00', '2024-01-09 10:00:00'),
('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'user10@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyY5Y5Y5Y5Yu', 'JKLMNOPQRSTUVWXY', true, '2024-01-10 10:00:00', '2024-01-10 10:00:00');

-- 2. ai_models 表 (10条) - 依赖 users
INSERT INTO public.ai_models (id, user_id, name, provider, enabled, api_key, base_url, model_name, created_at, updated_at) VALUES
('40000000-0000-0000-0000-000000000001', '11111111-1111-1111-1111-111111111111', 'OpenAI GPT-4', 'openai', true, 'sk-test-key-1111111111111111111111', 'https://api.openai.com/v1', 'gpt-4', '2024-01-01 11:00:00', '2024-01-01 11:00:00'),
('40000000-0000-0000-0000-000000000002', '22222222-2222-2222-2222-222222222222', 'Anthropic Claude', 'anthropic', true, 'sk-ant-test-key-2222222222222222222222', 'https://api.anthropic.com/v1', 'claude-3-opus', '2024-01-02 11:00:00', '2024-01-02 11:00:00'),
('40000000-0000-0000-0000-000000000003', '33333333-3333-3333-3333-333333333333', 'OpenAI GPT-3.5', 'openai', false, 'sk-test-key-3333333333333333333333', 'https://api.openai.com/v1', 'gpt-3.5-turbo', '2024-01-03 11:00:00', '2024-01-03 11:00:00'),
('40000000-0000-0000-0000-000000000004', '44444444-4444-4444-4444-444444444444', 'Anthropic Claude Sonnet', 'anthropic', true, 'sk-ant-test-key-4444444444444444444444', 'https://api.anthropic.com/v1', 'claude-3-sonnet', '2024-01-04 11:00:00', '2024-01-04 11:00:00'),
('40000000-0000-0000-0000-000000000005', '55555555-5555-5555-5555-555555555555', 'OpenAI GPT-4 Turbo', 'openai', true, 'sk-test-key-5555555555555555555555', 'https://api.openai.com/v1', 'gpt-4-turbo', '2024-01-05 11:00:00', '2024-01-05 11:00:00'),
('40000000-0000-0000-0000-000000000006', '66666666-6666-6666-6666-666666666666', 'Anthropic Claude Haiku', 'anthropic', false, 'sk-ant-test-key-6666666666666666666666', 'https://api.anthropic.com/v1', 'claude-3-haiku', '2024-01-06 11:00:00', '2024-01-06 11:00:00'),
('40000000-0000-0000-0000-000000000007', '77777777-7777-7777-7777-777777777777', 'OpenAI GPT-4o', 'openai', true, 'sk-test-key-7777777777777777777777', 'https://api.openai.com/v1', 'gpt-4o', '2024-01-07 11:00:00', '2024-01-07 11:00:00'),
('40000000-0000-0000-0000-000000000008', '88888888-8888-8888-8888-888888888888', 'Custom API Model', 'custom', true, 'custom-api-key-8888888888888888888888', 'https://api.custom.com/v1', 'custom-model-v1', '2024-01-08 11:00:00', '2024-01-08 11:00:00'),
('40000000-0000-0000-0000-000000000009', '99999999-9999-9999-9999-999999999999', 'OpenAI GPT-4 Mini', 'openai', false, 'sk-test-key-9999999999999999999999', 'https://api.openai.com/v1', 'gpt-4-mini', '2024-01-09 11:00:00', '2024-01-09 11:00:00'),
('40000000-0000-0000-0000-00000000000a', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'Anthropic Claude Opus', 'anthropic', true, 'sk-ant-test-key-bbbbbbbbbbbbbbbbbbbb', 'https://api.anthropic.com/v1', 'claude-3-opus-20240229', '2024-01-10 11:00:00', '2024-01-10 11:00:00');

-- 3. exchanges 表 (10条) - 依赖 users
INSERT INTO public.exchanges (id, user_id, name, type, enabled, api_key, secret_key, testnet, hyperliquid_wallet_addr, aster_user, aster_signer, aster_private_key, created_at, updated_at) VALUES
('50000000-0000-0000-0000-000000000001', '11111111-1111-1111-1111-111111111111', 'Binance Main', 'CEX', true, 'binance-api-key-1111111111111111111111', 'binance-secret-key-1111111111111111111111', false, '', '', '', '', '2024-01-01 12:00:00', '2024-01-01 12:00:00'),
('50000000-0000-0000-0000-000000000002', '22222222-2222-2222-2222-222222222222', 'OKX Main', 'CEX', true, 'okx-api-key-2222222222222222222222', 'okx-secret-key-2222222222222222222222', false, '', '', '', '', '2024-01-02 12:00:00', '2024-01-02 12:00:00'),
('50000000-0000-0000-0000-000000000003', '33333333-3333-3333-3333-333333333333', 'Hyperliquid Main', 'DEX', true, '', '', false, '0x1111111111111111111111111111111111111111', '', '', '', '2024-01-03 12:00:00', '2024-01-03 12:00:00'),
('50000000-0000-0000-0000-000000000004', '44444444-4444-4444-4444-444444444444', 'Aster Main', 'DEX', true, '', '', false, '', 'aster_user_4444444444444444444444', 'aster_signer_4444444444444444444444', 'aster_private_key_4444444444444444444444', '2024-01-04 12:00:00', '2024-01-04 12:00:00'),
('50000000-0000-0000-0000-000000000005', '55555555-5555-5555-5555-555555555555', 'Binance Testnet', 'CEX', false, 'binance-test-api-key-5555555555555555555555', 'binance-test-secret-key-5555555555555555555555', true, '', '', '', '', '2024-01-05 12:00:00', '2024-01-05 12:00:00'),
('50000000-0000-0000-0000-000000000006', '66666666-6666-6666-6666-666666666666', 'OKX Testnet', 'CEX', true, 'okx-test-api-key-6666666666666666666666', 'okx-test-secret-key-6666666666666666666666', true, '', '', '', '', '2024-01-06 12:00:00', '2024-01-06 12:00:00'),
('50000000-0000-0000-0000-000000000007', '77777777-7777-7777-7777-777777777777', 'Hyperliquid Testnet', 'DEX', false, '', '', true, '0x7777777777777777777777777777777777777777', '', '', '', '2024-01-07 12:00:00', '2024-01-07 12:00:00'),
('50000000-0000-0000-0000-000000000008', '88888888-8888-8888-8888-888888888888', 'Aster Testnet', 'DEX', true, '', '', true, '', 'aster_test_user_8888888888888888888888', 'aster_test_signer_8888888888888888888888', 'aster_test_private_key_8888888888888888888888', '2024-01-08 12:00:00', '2024-01-08 12:00:00'),
('50000000-0000-0000-0000-000000000009', '99999999-9999-9999-9999-999999999999', 'Bybit Main', 'CEX', true, 'bybit-api-key-9999999999999999999999', 'bybit-secret-key-9999999999999999999999', false, '', '', '', '', '2024-01-09 12:00:00', '2024-01-09 12:00:00'),
('50000000-0000-0000-0000-00000000000a', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'Gate.io Main', 'CEX', false, 'gate-api-key-bbbbbbbbbbbbbbbbbbbb', 'gate-secret-key-bbbbbbbbbbbbbbbbbbbb', false, '', '', '', '', '2024-01-10 12:00:00', '2024-01-10 12:00:00');

-- 4. prompt_templates 表 (10条) - 无依赖
INSERT INTO public.prompt_templates (id, name, content, description, created_at, updated_at) VALUES
('60000000-0000-0000-0000-000000000001', 'default', '你是专业的加密货币交易AI，在合约市场进行自主交易。\n\n# 核心目标\n\n最大化夏普比率（Sharpe Ratio）', '默认提示词模板', '2024-01-01 13:00:00', '2024-01-01 13:00:00'),
('60000000-0000-0000-0000-000000000002', 'conservative', '你是一个保守的交易AI，优先考虑风险控制。只在极高确定性时才开仓。', '保守型交易策略模板', '2024-01-02 13:00:00', '2024-01-02 13:00:00'),
('60000000-0000-0000-0000-000000000003', 'aggressive', '你是一个激进的交易AI，追求高收益，可以接受较高风险。', '激进型交易策略模板', '2024-01-03 13:00:00', '2024-01-03 13:00:00'),
('60000000-0000-0000-0000-000000000004', 'scalping', '你是一个高频交易AI，专注于短期价格波动，快速进出。', '高频交易策略模板', '2024-01-04 13:00:00', '2024-01-04 13:00:00'),
('60000000-0000-0000-0000-000000000005', 'swing', '你是一个波段交易AI，专注于中期趋势，持仓时间较长。', '波段交易策略模板', '2024-01-05 13:00:00', '2024-01-05 13:00:00'),
('60000000-0000-0000-0000-000000000006', 'trend_following', '你是一个趋势跟踪AI，专注于识别和跟随市场趋势。', '趋势跟踪策略模板', '2024-01-06 13:00:00', '2024-01-06 13:00:00'),
('60000000-0000-0000-0000-000000000007', 'mean_reversion', '你是一个均值回归AI，专注于价格偏离均值后的回归机会。', '均值回归策略模板', '2024-01-07 13:00:00', '2024-01-07 13:00:00'),
('60000000-0000-0000-0000-000000000008', 'arbitrage', '你是一个套利交易AI，专注于寻找不同市场间的价差机会。', '套利交易策略模板', '2024-01-08 13:00:00', '2024-01-08 13:00:00'),
('60000000-0000-0000-0000-000000000009', 'momentum', '你是一个动量交易AI，专注于捕捉价格动量突破的机会。', '动量交易策略模板', '2024-01-09 13:00:00', '2024-01-09 13:00:00'),
('60000000-0000-0000-0000-00000000000a', 'balanced', '你是一个平衡型交易AI，在风险和收益之间寻求平衡。', '平衡型交易策略模板', '2024-01-10 13:00:00', '2024-01-10 13:00:00');

-- 5. user_signal_sources 表 (10条) - 依赖 users，且 user_id 必须唯一
INSERT INTO public.user_signal_sources (id, user_id, coin_pool_url, oi_top_url, created_at, updated_at) VALUES
('70000000-0000-0000-0000-000000000001', '11111111-1111-1111-1111-111111111111', 'https://api.example.com/coin-pool/user1', 'https://api.example.com/oi-top/user1', '2024-01-01 14:00:00', '2024-01-01 14:00:00'),
('70000000-0000-0000-0000-000000000002', '22222222-2222-2222-2222-222222222222', 'https://api.example.com/coin-pool/user2', 'https://api.example.com/oi-top/user2', '2024-01-02 14:00:00', '2024-01-02 14:00:00'),
('70000000-0000-0000-0000-000000000003', '33333333-3333-3333-3333-333333333333', 'https://api.example.com/coin-pool/user3', 'https://api.example.com/oi-top/user3', '2024-01-03 14:00:00', '2024-01-03 14:00:00'),
('70000000-0000-0000-0000-000000000004', '44444444-4444-4444-4444-444444444444', 'https://api.example.com/coin-pool/user4', 'https://api.example.com/oi-top/user4', '2024-01-04 14:00:00', '2024-01-04 14:00:00'),
('70000000-0000-0000-0000-000000000005', '55555555-5555-5555-5555-555555555555', 'https://api.example.com/coin-pool/user5', 'https://api.example.com/oi-top/user5', '2024-01-05 14:00:00', '2024-01-05 14:00:00'),
('70000000-0000-0000-0000-000000000006', '66666666-6666-6666-6666-666666666666', 'https://api.example.com/coin-pool/user6', 'https://api.example.com/oi-top/user6', '2024-01-06 14:00:00', '2024-01-06 14:00:00'),
('70000000-0000-0000-0000-000000000007', '77777777-7777-7777-7777-777777777777', 'https://api.example.com/coin-pool/user7', 'https://api.example.com/oi-top/user7', '2024-01-07 14:00:00', '2024-01-07 14:00:00'),
('70000000-0000-0000-0000-000000000008', '88888888-8888-8888-8888-888888888888', 'https://api.example.com/coin-pool/user8', 'https://api.example.com/oi-top/user8', '2024-01-08 14:00:00', '2024-01-08 14:00:00'),
('70000000-0000-0000-0000-000000000009', '99999999-9999-9999-9999-999999999999', 'https://api.example.com/coin-pool/user9', 'https://api.example.com/oi-top/user9', '2024-01-09 14:00:00', '2024-01-09 14:00:00'),
('70000000-0000-0000-0000-00000000000a', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'https://api.example.com/coin-pool/user10', 'https://api.example.com/oi-top/user10', '2024-01-10 14:00:00', '2024-01-10 14:00:00');

-- 6. traders 表 (10条) - 依赖 users, ai_models, exchanges
-- 注意：每个 trader 的 user_id 必须与对应的 ai_model 和 exchange 的 user_id 一致
INSERT INTO public.traders (id, user_id, name, ai_model_id, exchange_id, initial_balance, scan_interval_minutes, is_running, btc_eth_leverage, altcoin_leverage, trading_symbols, use_default_coins, custom_coins, use_coin_pool, use_oi_top, use_inside_coins, system_prompt_template, custom_prompt, override_base_prompt, is_cross_margin, decision_graph_config, created_at, updated_at) VALUES
('10000000-0000-0000-0000-000000000001', '11111111-1111-1111-1111-111111111111', 'Trader Alpha', '40000000-0000-0000-0000-000000000001', '50000000-0000-0000-0000-000000000001', 10000.00000000, 3, true, 5, 5, 'BTC/USDT,ETH/USDT', true, '', true, true, false, 'default', '', false, true, '{"nodes": ["data_collector", "signal_analyzer", "ai_decision"]}', '2024-01-01 15:00:00', '2024-01-01 15:00:00'),
('10000000-0000-0000-0000-000000000002', '22222222-2222-2222-2222-222222222222', 'Trader Beta', '40000000-0000-0000-0000-000000000002', '50000000-0000-0000-0000-000000000002', 5000.00000000, 5, false, 3, 3, 'BTC/USDT,ETH/USDT,SOL/USDT', true, '', false, true, true, 'conservative', '', false, true, '{"nodes": ["data_collector", "risk_manager", "ai_decision"]}', '2024-01-02 15:00:00', '2024-01-02 15:00:00'),
('10000000-0000-0000-0000-000000000003', '33333333-3333-3333-3333-333333333333', 'Trader Gamma', '40000000-0000-0000-0000-000000000003', '50000000-0000-0000-0000-000000000003', 20000.00000000, 3, true, 10, 8, 'BTC/USDT', false, 'BTC/USDT,ETH/USDT,BNB/USDT', false, false, false, 'aggressive', 'Custom aggressive prompt', true, false, '{"nodes": ["data_collector", "signal_analyzer", "ai_decision", "order_executor"]}', '2024-01-03 15:00:00', '2024-01-03 15:00:00'),
('10000000-0000-0000-0000-000000000004', '44444444-4444-4444-4444-444444444444', 'Trader Delta', '40000000-0000-0000-0000-000000000004', '50000000-0000-0000-0000-000000000004', 15000.00000000, 1, true, 5, 5, '', true, '', true, false, false, 'scalping', '', false, true, '{"nodes": ["data_collector", "ai_decision"]}', '2024-01-04 15:00:00', '2024-01-04 15:00:00'),
('10000000-0000-0000-0000-000000000005', '55555555-5555-5555-5555-555555555555', 'Trader Epsilon', '40000000-0000-0000-0000-000000000005', '50000000-0000-0000-0000-000000000005', 8000.00000000, 10, false, 3, 3, 'BTC/USDT,ETH/USDT', true, '', false, false, false, 'swing', '', false, true, '{"nodes": ["data_collector", "signal_analyzer", "risk_manager", "ai_decision"]}', '2024-01-05 15:00:00', '2024-01-05 15:00:00'),
('10000000-0000-0000-0000-000000000006', '66666666-6666-6666-6666-666666666666', 'Trader Zeta', '40000000-0000-0000-0000-000000000006', '50000000-0000-0000-0000-000000000006', 12000.00000000, 3, true, 5, 5, 'BTC/USDT,ETH/USDT,SOL/USDT,AVAX/USDT', true, '', true, true, true, 'trend_following', '', false, true, '{"nodes": ["data_collector", "signal_analyzer", "ai_decision"]}', '2024-01-06 15:00:00', '2024-01-06 15:00:00'),
('10000000-0000-0000-0000-000000000007', '77777777-7777-7777-7777-777777777777', 'Trader Eta', '40000000-0000-0000-0000-000000000007', '50000000-0000-0000-0000-000000000007', 25000.00000000, 3, false, 5, 5, '', true, '', false, true, false, 'mean_reversion', '', false, true, '{"nodes": ["data_collector", "signal_analyzer", "risk_manager", "ai_decision"]}', '2024-01-07 15:00:00', '2024-01-07 15:00:00'),
('10000000-0000-0000-0000-000000000008', '88888888-8888-8888-8888-888888888888', 'Trader Theta', '40000000-0000-0000-0000-000000000008', '50000000-0000-0000-0000-000000000008', 3000.00000000, 2, true, 10, 10, 'BTC/USDT', false, 'BTC/USDT,ETH/USDT', true, false, false, 'arbitrage', 'Custom arbitrage strategy', true, false, '{"nodes": ["data_collector", "ai_decision", "order_executor"]}', '2024-01-08 15:00:00', '2024-01-08 15:00:00'),
('10000000-0000-0000-0000-000000000009', '99999999-9999-9999-9999-999999999999', 'Trader Iota', '40000000-0000-0000-0000-000000000009', '50000000-0000-0000-0000-000000000009', 18000.00000000, 3, true, 5, 5, 'BTC/USDT,ETH/USDT,SOL/USDT', true, '', true, false, false, 'momentum', '', false, true, '{"nodes": ["data_collector", "signal_analyzer", "ai_decision"]}', '2024-01-09 15:00:00', '2024-01-09 15:00:00'),
('10000000-0000-0000-0000-00000000000a', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'Trader Kappa', '40000000-0000-0000-0000-00000000000a', '50000000-0000-0000-0000-00000000000a', 6000.00000000, 5, false, 3, 3, 'BTC/USDT,ETH/USDT', true, '', false, false, false, 'balanced', '', false, true, '{"nodes": ["data_collector", "signal_analyzer", "risk_manager", "ai_decision", "order_executor"]}', '2024-01-10 15:00:00', '2024-01-10 15:00:00');

-- 7. trade_records 表 (10条) - 依赖 traders
INSERT INTO public.trade_records (id, trader_id, symbol, side, amount, price, leverage, order_id, status, created_at, updated_at) VALUES
('20000000-0000-0000-0000-000000000001', '10000000-0000-0000-0000-000000000001', 'BTC/USDT', 'buy', 0.10000000, 45000.00000000, 5, 'order-1111111111111111111111', 'filled', '2024-01-01 16:00:00', '2024-01-01 16:00:05'),
('20000000-0000-0000-0000-000000000002', '10000000-0000-0000-0000-000000000002', 'ETH/USDT', 'sell', 1.50000000, 2800.00000000, 3, 'order-2222222222222222222222', 'filled', '2024-01-02 16:00:00', '2024-01-02 16:00:05'),
('20000000-0000-0000-0000-000000000003', '10000000-0000-0000-0000-000000000003', 'BTC/USDT', 'buy', 0.20000000, 45500.00000000, 10, 'order-3333333333333333333333', 'pending', '2024-01-03 16:00:00', '2024-01-03 16:00:00'),
('20000000-0000-0000-0000-000000000004', '10000000-0000-0000-0000-000000000004', 'SOL/USDT', 'buy', 50.00000000, 95.50000000, 5, 'order-4444444444444444444444', 'filled', '2024-01-04 16:00:00', '2024-01-04 16:00:03'),
('20000000-0000-0000-0000-000000000005', '10000000-0000-0000-0000-000000000005', 'BTC/USDT', 'sell', 0.05000000, 46000.00000000, 3, 'order-5555555555555555555555', 'filled', '2024-01-05 16:00:00', '2024-01-05 16:00:05'),
('20000000-0000-0000-0000-000000000006', '10000000-0000-0000-0000-000000000006', 'ETH/USDT', 'buy', 2.00000000, 2750.00000000, 5, 'order-6666666666666666666666', 'filled', '2024-01-06 16:00:00', '2024-01-06 16:00:05'),
('20000000-0000-0000-0000-000000000007', '10000000-0000-0000-0000-000000000007', 'AVAX/USDT', 'sell', 100.00000000, 35.20000000, 5, 'order-7777777777777777777777', 'cancelled', '2024-01-07 16:00:00', '2024-01-07 16:00:10'),
('20000000-0000-0000-0000-000000000008', '10000000-0000-0000-0000-000000000008', 'BTC/USDT', 'buy', 0.15000000, 44800.00000000, 10, 'order-8888888888888888888888', 'filled', '2024-01-08 16:00:00', '2024-01-08 16:00:05'),
('20000000-0000-0000-0000-000000000009', '10000000-0000-0000-0000-000000000009', 'SOL/USDT', 'sell', 30.00000000, 98.00000000, 5, 'order-9999999999999999999999', 'filled', '2024-01-09 16:00:00', '2024-01-09 16:00:05'),
('20000000-0000-0000-0000-00000000000a', '10000000-0000-0000-0000-00000000000a', 'ETH/USDT', 'buy', 1.00000000, 2700.00000000, 3, 'order-bbbbbbbbbbbbbbbbbbbb', 'pending', '2024-01-10 16:00:00', '2024-01-10 16:00:00');

-- 8. decision_logs 表 (10条) - 依赖 traders
INSERT INTO public.decision_logs (id, trader_id, symbol, decision_state, decision_result, reasoning, confidence, created_at, updated_at) VALUES
('30000000-0000-0000-0000-000000000001', '10000000-0000-0000-0000-000000000001', 'BTC/USDT', '{"price": 45000, "rsi": 55, "macd": "bullish", "volume": "high"}', 'buy', 'Strong bullish signal with high volume and positive MACD. RSI indicates healthy momentum.', 0.8500, '2024-01-01 17:00:00', '2024-01-01 17:00:00'),
('30000000-0000-0000-0000-000000000002', '10000000-0000-0000-0000-000000000002', 'ETH/USDT', '{"price": 2800, "rsi": 65, "macd": "bearish", "volume": "medium"}', 'sell', 'RSI overbought with bearish MACD divergence. Taking profit on existing position.', 0.7200, '2024-01-02 17:00:00', '2024-01-02 17:00:00'),
('30000000-0000-0000-0000-000000000003', '10000000-0000-0000-0000-000000000003', 'BTC/USDT', '{"price": 45500, "rsi": 50, "macd": "neutral", "volume": "low"}', 'wait', 'Market conditions unclear. Low volume and neutral indicators suggest waiting for clearer signal.', 0.4500, '2024-01-03 17:00:00', '2024-01-03 17:00:00'),
('30000000-0000-0000-0000-000000000004', '10000000-0000-0000-0000-000000000004', 'SOL/USDT', '{"price": 95.5, "rsi": 40, "macd": "bullish", "volume": "high"}', 'buy', 'Oversold condition with bullish MACD crossover. High volume confirms strong buying interest.', 0.8800, '2024-01-04 17:00:00', '2024-01-04 17:00:00'),
('30000000-0000-0000-0000-000000000005', '10000000-0000-0000-0000-000000000005', 'BTC/USDT', '{"price": 46000, "rsi": 70, "macd": "bearish", "volume": "medium"}', 'sell', 'Overbought RSI with bearish MACD. Profit target reached, closing position.', 0.7500, '2024-01-05 17:00:00', '2024-01-05 17:00:00'),
('30000000-0000-0000-0000-000000000006', '10000000-0000-0000-0000-000000000006', 'ETH/USDT', '{"price": 2750, "rsi": 45, "macd": "bullish", "volume": "high"}', 'buy', 'Strong uptrend with bullish MACD and increasing volume. Entry point identified.', 0.8200, '2024-01-06 17:00:00', '2024-01-06 17:00:00'),
('30000000-0000-0000-0000-000000000007', '10000000-0000-0000-0000-000000000007', 'AVAX/USDT', '{"price": 35.2, "rsi": 60, "macd": "neutral", "volume": "low"}', 'hold', 'Position in profit but signals mixed. Holding for better exit opportunity.', 0.6000, '2024-01-07 17:00:00', '2024-01-07 17:00:00'),
('30000000-0000-0000-0000-000000000008', '10000000-0000-0000-0000-000000000008', 'BTC/USDT', '{"price": 44800, "rsi": 35, "macd": "bullish", "volume": "very_high"}', 'buy', 'Oversold bounce with extremely high volume. Strong reversal signal detected.', 0.9200, '2024-01-08 17:00:00', '2024-01-08 17:00:00'),
('30000000-0000-0000-0000-000000000009', '10000000-0000-0000-0000-000000000009', 'SOL/USDT', '{"price": 98, "rsi": 75, "macd": "bearish", "volume": "high"}', 'sell', 'Extreme overbought condition. Bearish divergence forming. Taking profits.', 0.7800, '2024-01-09 17:00:00', '2024-01-09 17:00:00'),
('30000000-0000-0000-0000-00000000000a', '10000000-0000-0000-0000-00000000000a', 'ETH/USDT', '{"price": 2700, "rsi": 55, "macd": "bullish", "volume": "medium"}', 'wait', 'Moderate bullish signals but volume insufficient. Waiting for confirmation.', 0.5500, '2024-01-10 17:00:00', '2024-01-10 17:00:00');

-- 9. system_config 表 (10条) - 无依赖
INSERT INTO public.system_config (key, value, updated_at) VALUES
('max_leverage', '10', '2024-01-01 18:00:00'),
('min_balance', '100', '2024-01-02 18:00:00'),
('default_scan_interval', '3', '2024-01-03 18:00:00'),
('max_open_positions', '5', '2024-01-04 18:00:00'),
('risk_limit_per_trade', '0.02', '2024-01-05 18:00:00'),
('enable_notifications', 'true', '2024-01-06 18:00:00'),
('api_rate_limit', '100', '2024-01-07 18:00:00'),
('default_timeout', '30', '2024-01-08 18:00:00'),
('log_level', 'INFO', '2024-01-09 18:00:00'),
('maintenance_mode', 'false', '2024-01-10 18:00:00');
