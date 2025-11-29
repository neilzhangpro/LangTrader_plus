--
-- PostgreSQL database dump
--

\restrict HO3chExX8Ms0c2jaLEZrA9TMb7O1uhbrO2RCSorRFTmFLQ9mfuecZVOe0MMoUc1

-- Dumped from database version 14.19 (Homebrew)
-- Dumped by pg_dump version 14.19 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: update_updated_at_column(); Type: FUNCTION; Schema: public; Owner: tomiezhang
--

CREATE FUNCTION public.update_updated_at_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_updated_at_column() OWNER TO tomiezhang;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: ai_models; Type: TABLE; Schema: public; Owner: tomiezhang
--

CREATE TABLE public.ai_models (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    name character varying(255) NOT NULL,
    provider character varying(50) NOT NULL,
    enabled boolean DEFAULT false,
    api_key text DEFAULT ''::text,
    base_url text DEFAULT ''::text,
    model_name text DEFAULT ''::text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.ai_models OWNER TO tomiezhang;

--
-- Name: decision_logs; Type: TABLE; Schema: public; Owner: tomiezhang
--

CREATE TABLE public.decision_logs (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    trader_id uuid NOT NULL,
    symbol character varying(50) NOT NULL,
    decision_state jsonb NOT NULL,
    decision_result character varying(50),
    reasoning text,
    confidence numeric(5,4),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone
);


ALTER TABLE public.decision_logs OWNER TO tomiezhang;

--
-- Name: exchanges; Type: TABLE; Schema: public; Owner: tomiezhang
--

CREATE TABLE public.exchanges (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    name character varying(255) NOT NULL,
    type character varying(10) NOT NULL,
    enabled boolean DEFAULT false,
    api_key text DEFAULT ''::text,
    secret_key text DEFAULT ''::text,
    testnet boolean DEFAULT false,
    hyperliquid_wallet_addr character varying(255) DEFAULT ''::character varying,
    aster_user character varying(255) DEFAULT ''::character varying,
    aster_signer character varying(255) DEFAULT ''::character varying,
    aster_private_key text DEFAULT ''::text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.exchanges OWNER TO tomiezhang;

--
-- Name: prompt_templates; Type: TABLE; Schema: public; Owner: tomiezhang
--

CREATE TABLE public.prompt_templates (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    name character varying(255) DEFAULT 'default'::character varying NOT NULL,
    content text DEFAULT '你是专业的加密货币交易AI，在合约市场进行自主交易。

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
大多数时候应该是 `wait` 或 `hold`，只在极佳机会时才开仓。

# 交易哲学 & 最佳实践

## 核心原则：

资金保全第一：保护资本比追求收益更重要

纪律胜于情绪：执行你的退出方案，不随意移动止损或目标

质量优于数量：少量高信念交易胜过大量低信念交易

适应波动性：根据市场条件调整仓位

尊重趋势：不要与强趋势作对

## 常见误区避免：

过度交易：频繁交易导致费用侵蚀利润

复仇式交易：亏损后立即加码试图"翻本"

分析瘫痪：过度等待完美信号，导致失机

忽视相关性：BTC常引领山寨币，须优先观察BTC

过度杠杆：放大收益同时放大亏损

#交易频率认知

量化标准:
- 优秀交易员：每天2-4笔 = 每小时0.1-0.2笔
- 过度交易：每小时>2笔 = 严重问题
- 最佳节奏：开仓后持有至少30-60分钟

自查:
如果你发现自己每个周期都在交易 → 说明标准太低
如果你发现持仓<30分钟就平仓 → 说明太急躁

# 开仓标准（严格）

只在强信号时开仓，不确定就观望。

你拥有的完整数据：
- 原始序列：3分钟价格序列(MidPrices数组) + 4小时K线序列
- 技术序列：EMA20序列、MACD序列、RSI7序列、RSI14序列
- 资金序列：成交量序列、持仓量(OI)序列、资金费率
- 筛选标记：AI500评分 / OI_Top排名（如果有标注）

分析方法（完全由你自主决定）：
- 自由运用序列数据，你可以做但不限于趋势分析、形态识别、支撑阻力、技术阻力位、斐波那契、波动带计算
- 多维度交叉验证（价格+量+OI+指标+序列形态）
- 用你认为最有效的方法发现高确定性机会
- 综合信心度 ≥ 75 才开仓

避免低质量信号：
- 单一维度（只看一个指标）
- 相互矛盾（涨但量萎缩）
- 横盘震荡
- 刚平仓不久（<15分钟）

# 夏普比率自我进化

每次你会收到夏普比率作为绩效反馈（周期级别）：

夏普比率 < -0.5 (持续亏损):
  → 停止交易，连续观望至少6个周期（18分钟）
  → 深度反思：
     • 交易频率过高？（每小时>2次就是过度）
     • 持仓时间过短？（<30分钟就是过早平仓）
     • 信号强度不足？（信心度<75）
夏普比率 -0.5 ~ 0 (轻微亏损):
  → 严格控制：只做信心度>80的交易
  → 减少交易频率：每小时最多1笔新开仓
  → 耐心持仓：至少持有30分钟以上

夏普比率 0 ~ 0.7 (正收益):
  → 维持当前策略

夏普比率 > 0.7 (优异表现):
  → 可适度扩大仓位

关键: 夏普比率是唯一指标，它会自然惩罚频繁交易和过度进出。

#决策流程

1. 分析夏普比率: 当前策略是否有效？需要调整吗？
2. 评估持仓: 趋势是否改变？是否该止盈/止损？
3. 寻找新机会: 有强信号吗？多空机会？
4. 输出决策: 思维链分析 + JSON

---

记住:
- 目标是夏普比率，不是交易频率
- 宁可错过，不做低质量交易
- 风险回报比1:3是底线'::text NOT NULL,
    description text DEFAULT '默认提示词模板'::text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.prompt_templates OWNER TO tomiezhang;

--
-- Name: system_config; Type: TABLE; Schema: public; Owner: tomiezhang
--

CREATE TABLE public.system_config (
    key character varying(255) NOT NULL,
    value text NOT NULL,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.system_config OWNER TO tomiezhang;

--
-- Name: trade_records; Type: TABLE; Schema: public; Owner: tomiezhang
--

CREATE TABLE public.trade_records (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    trader_id uuid NOT NULL,
    symbol character varying(50) NOT NULL,
    side character varying(10) NOT NULL,
    amount numeric(20,8) NOT NULL,
    price numeric(20,8) NOT NULL,
    leverage integer DEFAULT 1,
    order_id character varying(255),
    status character varying(50) DEFAULT 'pending'::character varying,
    updated_at timestamp without time zone,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.trade_records OWNER TO tomiezhang;

--
-- Name: traders; Type: TABLE; Schema: public; Owner: tomiezhang
--

CREATE TABLE public.traders (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    name character varying(255) NOT NULL,
    ai_model_id uuid NOT NULL,
    exchange_id uuid NOT NULL,
    initial_balance numeric(20,8) NOT NULL,
    scan_interval_minutes integer DEFAULT 3,
    is_running boolean DEFAULT false,
    btc_eth_leverage integer DEFAULT 5,
    altcoin_leverage integer DEFAULT 5,
    trading_symbols text DEFAULT ''::text,
    use_default_coins boolean DEFAULT true,
    custom_coins text DEFAULT ''::text,
    use_coin_pool boolean DEFAULT false,
    use_oi_top boolean DEFAULT false,
    use_inside_coins boolean DEFAULT false,
    system_prompt_template character varying(255) DEFAULT 'default'::character varying,
    custom_prompt text DEFAULT ''::text,
    override_base_prompt boolean DEFAULT false,
    is_cross_margin boolean DEFAULT true,
    decision_graph_config jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.traders OWNER TO tomiezhang;

--
-- Name: user_signal_sources; Type: TABLE; Schema: public; Owner: tomiezhang
--

CREATE TABLE public.user_signal_sources (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    coin_pool_url text DEFAULT ''::text,
    oi_top_url text DEFAULT ''::text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.user_signal_sources OWNER TO tomiezhang;

--
-- Name: users; Type: TABLE; Schema: public; Owner: tomiezhang
--

CREATE TABLE public.users (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    email character varying(255) NOT NULL,
    password_hash character varying(255) NOT NULL,
    otp_secret character varying(32),
    otp_verified boolean DEFAULT false,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.users OWNER TO tomiezhang;

--
-- Name: ai_models ai_models_pkey; Type: CONSTRAINT; Schema: public; Owner: tomiezhang
--

ALTER TABLE ONLY public.ai_models
    ADD CONSTRAINT ai_models_pkey PRIMARY KEY (id);


--
-- Name: decision_logs decision_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: tomiezhang
--

ALTER TABLE ONLY public.decision_logs
    ADD CONSTRAINT decision_logs_pkey PRIMARY KEY (id);


--
-- Name: exchanges exchanges_pkey; Type: CONSTRAINT; Schema: public; Owner: tomiezhang
--

ALTER TABLE ONLY public.exchanges
    ADD CONSTRAINT exchanges_pkey PRIMARY KEY (id);


--
-- Name: prompt_templates prompt_templates_pkey; Type: CONSTRAINT; Schema: public; Owner: tomiezhang
--

ALTER TABLE ONLY public.prompt_templates
    ADD CONSTRAINT prompt_templates_pkey PRIMARY KEY (id);


--
-- Name: system_config system_config_pkey; Type: CONSTRAINT; Schema: public; Owner: tomiezhang
--

ALTER TABLE ONLY public.system_config
    ADD CONSTRAINT system_config_pkey PRIMARY KEY (key);


--
-- Name: trade_records trade_records_pkey; Type: CONSTRAINT; Schema: public; Owner: tomiezhang
--

ALTER TABLE ONLY public.trade_records
    ADD CONSTRAINT trade_records_pkey PRIMARY KEY (id);


--
-- Name: traders traders_pkey; Type: CONSTRAINT; Schema: public; Owner: tomiezhang
--

ALTER TABLE ONLY public.traders
    ADD CONSTRAINT traders_pkey PRIMARY KEY (id);


--
-- Name: user_signal_sources user_signal_sources_pkey; Type: CONSTRAINT; Schema: public; Owner: tomiezhang
--

ALTER TABLE ONLY public.user_signal_sources
    ADD CONSTRAINT user_signal_sources_pkey PRIMARY KEY (id);


--
-- Name: user_signal_sources user_signal_sources_user_id_key; Type: CONSTRAINT; Schema: public; Owner: tomiezhang
--

ALTER TABLE ONLY public.user_signal_sources
    ADD CONSTRAINT user_signal_sources_user_id_key UNIQUE (user_id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: tomiezhang
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: tomiezhang
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: idx_ai_models_user_id; Type: INDEX; Schema: public; Owner: tomiezhang
--

CREATE INDEX idx_ai_models_user_id ON public.ai_models USING btree (user_id);


--
-- Name: idx_decision_logs_created_at; Type: INDEX; Schema: public; Owner: tomiezhang
--

CREATE INDEX idx_decision_logs_created_at ON public.decision_logs USING btree (created_at);


--
-- Name: idx_decision_logs_trader_id; Type: INDEX; Schema: public; Owner: tomiezhang
--

CREATE INDEX idx_decision_logs_trader_id ON public.decision_logs USING btree (trader_id);


--
-- Name: idx_exchanges_user_id; Type: INDEX; Schema: public; Owner: tomiezhang
--

CREATE INDEX idx_exchanges_user_id ON public.exchanges USING btree (user_id);


--
-- Name: idx_trade_records_created_at; Type: INDEX; Schema: public; Owner: tomiezhang
--

CREATE INDEX idx_trade_records_created_at ON public.trade_records USING btree (created_at);


--
-- Name: idx_trade_records_trader_id; Type: INDEX; Schema: public; Owner: tomiezhang
--

CREATE INDEX idx_trade_records_trader_id ON public.trade_records USING btree (trader_id);


--
-- Name: idx_traders_ai_model_id; Type: INDEX; Schema: public; Owner: tomiezhang
--

CREATE INDEX idx_traders_ai_model_id ON public.traders USING btree (ai_model_id);


--
-- Name: idx_traders_exchange_id; Type: INDEX; Schema: public; Owner: tomiezhang
--

CREATE INDEX idx_traders_exchange_id ON public.traders USING btree (exchange_id);


--
-- Name: idx_traders_is_running; Type: INDEX; Schema: public; Owner: tomiezhang
--

CREATE INDEX idx_traders_is_running ON public.traders USING btree (is_running);


--
-- Name: idx_traders_user_id; Type: INDEX; Schema: public; Owner: tomiezhang
--

CREATE INDEX idx_traders_user_id ON public.traders USING btree (user_id);


--
-- Name: ai_models update_ai_models_updated_at; Type: TRIGGER; Schema: public; Owner: tomiezhang
--

CREATE TRIGGER update_ai_models_updated_at BEFORE UPDATE ON public.ai_models FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: exchanges update_exchanges_updated_at; Type: TRIGGER; Schema: public; Owner: tomiezhang
--

CREATE TRIGGER update_exchanges_updated_at BEFORE UPDATE ON public.exchanges FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: prompt_templates update_prompt_templates_updated_at; Type: TRIGGER; Schema: public; Owner: tomiezhang
--

CREATE TRIGGER update_prompt_templates_updated_at BEFORE UPDATE ON public.prompt_templates FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: system_config update_system_config_updated_at; Type: TRIGGER; Schema: public; Owner: tomiezhang
--

CREATE TRIGGER update_system_config_updated_at BEFORE UPDATE ON public.system_config FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: traders update_traders_updated_at; Type: TRIGGER; Schema: public; Owner: tomiezhang
--

CREATE TRIGGER update_traders_updated_at BEFORE UPDATE ON public.traders FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: user_signal_sources update_user_signal_sources_updated_at; Type: TRIGGER; Schema: public; Owner: tomiezhang
--

CREATE TRIGGER update_user_signal_sources_updated_at BEFORE UPDATE ON public.user_signal_sources FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: users update_users_updated_at; Type: TRIGGER; Schema: public; Owner: tomiezhang
--

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON public.users FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: ai_models ai_models_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: tomiezhang
--

ALTER TABLE ONLY public.ai_models
    ADD CONSTRAINT ai_models_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: decision_logs decision_logs_trader_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: tomiezhang
--

ALTER TABLE ONLY public.decision_logs
    ADD CONSTRAINT decision_logs_trader_id_fkey FOREIGN KEY (trader_id) REFERENCES public.traders(id) ON DELETE CASCADE;


--
-- Name: exchanges exchanges_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: tomiezhang
--

ALTER TABLE ONLY public.exchanges
    ADD CONSTRAINT exchanges_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: trade_records trade_records_trader_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: tomiezhang
--

ALTER TABLE ONLY public.trade_records
    ADD CONSTRAINT trade_records_trader_id_fkey FOREIGN KEY (trader_id) REFERENCES public.traders(id) ON DELETE CASCADE;


--
-- Name: traders traders_ai_model_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: tomiezhang
--

ALTER TABLE ONLY public.traders
    ADD CONSTRAINT traders_ai_model_id_fkey FOREIGN KEY (ai_model_id) REFERENCES public.ai_models(id);


--
-- Name: traders traders_exchange_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: tomiezhang
--

ALTER TABLE ONLY public.traders
    ADD CONSTRAINT traders_exchange_id_fkey FOREIGN KEY (exchange_id) REFERENCES public.exchanges(id);


--
-- Name: traders traders_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: tomiezhang
--

ALTER TABLE ONLY public.traders
    ADD CONSTRAINT traders_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: user_signal_sources user_signal_sources_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: tomiezhang
--

ALTER TABLE ONLY public.user_signal_sources
    ADD CONSTRAINT user_signal_sources_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict HO3chExX8Ms0c2jaLEZrA9TMb7O1uhbrO2RCSorRFTmFLQ9mfuecZVOe0MMoUc1

