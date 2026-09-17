# Quality Report — Phase 3B & Phase 4

## Status & Summary
- **Execution Target**: 50
- **Final Accepted Qualified Records**: 50
- **Target Reached**: YES
- **Audit Output Log**: `data/audits/phase_3b_audit.jsonl`
- **Date**: 2026-09-17

## Deterministic Audit Breakdown
- **Total Records Audited**: 50
- **PASS (Zero Semantic Issues)**: 49
- **CORRECTED (Semantics Corrected)**: 1
- **REVIEW_REQUIRED**: 0
- **REJECT**: 0

## Verification & Semantic Precision Metrics
- **Official External Website URLs**: 36
- **Website Verified (`website_verified = True`)**: 36 (True ONLY for verified external homepages)
- **GitHub Repository Verified (`github_repository_verified = True`)**: 50
- **Verified Brand Logos (`logo_verified = True`)**: 35
- **GitHub Social Preview Fallbacks (`logo_source = 'github_social_preview'`)**: 15 (`logo_verified = False`)

## Discovery & Qualification Metrics
- **Total Candidates Discovered**: 73
- **Pages Fetched**: 3
- **QUALIFIED_TOOL**: 57
- **REVIEW_REQUIRED**: 11
- **REJECTED_NON_TOOL**: 5

## README & Description Grounding Metrics
- **README Found**: 0
- **README Missing**: 57
- **Grounded Descriptions**: 50 / 50
- **Description Source Types**:
  - `GITHUB_REPOSITORY_DESCRIPTION`: 50

## Category Distribution (Accepted Dataset)
- **MCP**: 10
- **Agents**: 25
- **Models**: 12
- **Developer Tools**: 22
- **Productivity**: 3
- **Automation**: 5
- **Research**: 2
- **Design**: 2
- **Video**: 2
- **Audio**: 1
- **Coding**: 2
- **Data Analysis**: 2
- **Marketing**: 1
- **AI Assistants**: 1

## GitHub Star Metrics
- **Records with github_stars**: 50
- **Minimum Stars**: 1483
- **Maximum Stars**: 133215
- **Median Stars**: 3595

## Deduplication & Validation Metrics
- **Duplicates Merged**: 0
- **Accepted**: 50
- **Rejected Validation**: 7

## Top Qualification & Validation Rejection Reasons
- `REVIEW_REQUIRED: Name matches negative pattern: ^awesome[\-_], Negative topics: awesome, awesome-list`: 4
- `REJECTED_NON_TOOL: Name matches negative pattern: ^awesome[\-_], Description matches non-tool pattern: '\bcurated\s+list\b'`: 3
- `REVIEW_REQUIRED: Name matches negative pattern: [\-_]template[s]?$, Negative topics: boilerplate, template`: 1
- `Validation: Identity Verification Failed: Network or SSL error: [Errno 11002] getaddrinfo failed`: 1
- `Validation: Identity Verification Failed: HTTP 200 OK, but domain/title content mismatched: 'Skill Seekers - The Data Layer for AI Sy'`: 1
- `REVIEW_REQUIRED: Repository is archived, Positive: Positive topics: ai-tools, automation, tool`: 1
- `REVIEW_REQUIRED: Repository is archived, Positive: Positive topics: agent, agents, ai-agents, ai-tools, automation, mcp`: 1
- `REVIEW_REQUIRED: Description matches non-tool pattern: '\bcollection\s+of\b', Negative topics: awesome-list`: 1
- `Validation: Identity Verification Failed: Network or SSL error: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (`: 1
- `Validation: Identity Verification Failed: HTTP 200 OK, but domain/title content mismatched: 'Build content creation into your app | U'`: 1

# Phase 4 — LLM Orchestration

## Provider Fallback Architecture & Configuration
- **Primary Provider**: Gemini Flash (`GEMINI_API_KEY`)
- **Fallback 1**: Groq Llama-3 (`GROQ_API_KEY`)
- **Fallback 2**: DeepSeek (`DEEPSEEK_API_KEY`)
- **Test & Safe Mode**: Deterministic source-derived fallback when API credentials are absent (`llm_enrichment_status = NOT_CONFIGURED`).

## LLM Generation & Orchestration Metrics
- **Total Records Sent to LLM**: 0
- **Gemini Attempts / Successes / Failures**: 0 / 0 / 0
- **Groq Attempts / Successes / Failures**: 0 / 0 / 0
- **DeepSeek Attempts / Successes / Failures**: 0 / 0 / 0
- **Total Fallback Events**: 0
- **Malformed Responses**: 0
- **Grounded LLM Descriptions**: 0
- **Ungrounded LLM Responses**: 0
- **Records with No Usable Description**: 0

## Processed Records LLM Detail

### 1. cc-switch
- **Description**: A cross-platform desktop All-in-One assistant for Claude Code, Codex, OpenCode, OpenClaw, Grok Build & Hermes Agent. Only official website: ccswitch.io
- **LLM Provider Used**: NONE
- **Description Source Type**: GITHUB_REPOSITORY_DESCRIPTION
- **Description Source URL**: https://github.com/farion1231/cc-switch
- **Description Grounded**: True
- **LLM Enrichment Status**: DISABLED
- **Description Generation Method**: EXTRACTED_FROM_SOURCE

### 2. browser-use
- **Description**: Agents that use the browser.
- **LLM Provider Used**: NONE
- **Description Source Type**: GITHUB_REPOSITORY_DESCRIPTION
- **Description Source URL**: https://github.com/browser-use/browser-use
- **Description Grounded**: True
- **LLM Enrichment Status**: DISABLED
- **Description Generation Method**: EXTRACTED_FROM_SOURCE

### 3. private-gpt
- **Description**: Complete API layer for private AI applications on local models: RAG, skills, tools, MCP, text-to-sql, and more. Works with any OpenAI-compatible inference server.
- **LLM Provider Used**: NONE
- **Description Source Type**: GITHUB_REPOSITORY_DESCRIPTION
- **Description Source URL**: https://github.com/zylon-ai/private-gpt
- **Description Grounded**: True
- **LLM Enrichment Status**: DISABLED
- **Description Generation Method**: EXTRACTED_FROM_SOURCE

### 4. medusa
- **Description**: The world's most flexible commerce platform for agents and developers
- **LLM Provider Used**: NONE
- **Description Source Type**: GITHUB_REPOSITORY_DESCRIPTION
- **Description Source URL**: https://github.com/medusajs/medusa
- **Description Grounded**: True
- **LLM Enrichment Status**: DISABLED
- **Description Generation Method**: EXTRACTED_FROM_SOURCE

### 5. prompt-optimizer
- **Description**: An AI prompt optimizer for writing better prompts and getting better AI results.
- **LLM Provider Used**: NONE
- **Description Source Type**: GITHUB_REPOSITORY_DESCRIPTION
- **Description Source URL**: https://github.com/linshenkx/prompt-optimizer
- **Description Grounded**: True
- **LLM Enrichment Status**: DISABLED
- **Description Generation Method**: EXTRACTED_FROM_SOURCE

### 6. openclaude
- **Description**: runs anywhere. uses anything
- **LLM Provider Used**: NONE
- **Description Source Type**: GITHUB_REPOSITORY_DESCRIPTION
- **Description Source URL**: https://github.com/Gitlawb/openclaude
- **Description Grounded**: True
- **LLM Enrichment Status**: DISABLED
- **Description Generation Method**: EXTRACTED_FROM_SOURCE

### 7. OpenCLI
- **Description**: Make Any Website into CLI & Use your logged-in browser by AI agent.
- **LLM Provider Used**: NONE
- **Description Source Type**: GITHUB_REPOSITORY_DESCRIPTION
- **Description Source URL**: https://github.com/jackwener/OpenCLI
- **Description Grounded**: True
- **LLM Enrichment Status**: DISABLED
- **Description Generation Method**: EXTRACTED_FROM_SOURCE

### 8. nocobase
- **Description**: NocoBase is an open-source AI + no-code platform for building business systems fast. Instead of generating everything from scratch, AI works on top of production-proven infrastructure and a WYSIWYG no-code interface, so you get both speed and reliability.
- **LLM Provider Used**: NONE
- **Description Source Type**: GITHUB_REPOSITORY_DESCRIPTION
- **Description Source URL**: https://github.com/nocobase/nocobase
- **Description Grounded**: True
- **LLM Enrichment Status**: DISABLED
- **Description Generation Method**: EXTRACTED_FROM_SOURCE

### 9. Auto-claude-code-research-in-sleep
- **Description**: ARIS ⚔️ (Auto-Research-In-Sleep) — Lightweight Markdown-only skills for autonomous ML research: cross-model review loops, idea discovery, and experiment automation. No framework, no lock-in — works with Claude Code, Codex, OpenClaw, or any LLM agent.
- **LLM Provider Used**: NONE
- **Description Source Type**: GITHUB_REPOSITORY_DESCRIPTION
- **Description Source URL**: https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep
- **Description Grounded**: True
- **LLM Enrichment Status**: DISABLED
- **Description Generation Method**: EXTRACTED_FROM_SOURCE

### 10. opencodex
- **Description**: Universal provider proxy for OpenAI Codex & Claude Code — use any LLM (Claude, Gemini, Grok, DeepSeek, Ollama...) with Codex CLI, App, SDK, and Claude Code
- **LLM Provider Used**: NONE
- **Description Source Type**: GITHUB_REPOSITORY_DESCRIPTION
- **Description Source URL**: https://github.com/lidge-jun/opencodex
- **Description Grounded**: True
- **LLM Enrichment Status**: DISABLED
- **Description Generation Method**: EXTRACTED_FROM_SOURCE

### 11. nanobrowser
- **Description**: Open-Source Chrome extension for AI-powered web automation. Run multi-agent workflows using your own LLM API key. Alternative to OpenAI Operator.
- **LLM Provider Used**: NONE
- **Description Source Type**: GITHUB_REPOSITORY_DESCRIPTION
- **Description Source URL**: https://github.com/nanobrowser/nanobrowser
- **Description Grounded**: True
- **LLM Enrichment Status**: DISABLED
- **Description Generation Method**: EXTRACTED_FROM_SOURCE

### 12. ccstatusline
- **Description**: 🚀 Beautiful highly customizable statusline for Claude Code CLI with powerline support, themes, and more.
- **LLM Provider Used**: NONE
- **Description Source Type**: GITHUB_REPOSITORY_DESCRIPTION
- **Description Source URL**: https://github.com/sirmalloc/ccstatusline
- **Description Grounded**: True
- **LLM Enrichment Status**: DISABLED
- **Description Generation Method**: EXTRACTED_FROM_SOURCE

### 13. ChatGPT-Shortcut
- **Description**: Stop writing prompts from scratch — a searchable prompt library for ChatGPT, Claude, Gemini and Cursor · Русский 한국어 العربية हिन्दी ไทย | 别再从头写提示词:现成的拿来就用,好用的收进自己的库
- **LLM Provider Used**: NONE
- **Description Source Type**: GITHUB_REPOSITORY_DESCRIPTION
- **Description Source URL**: https://github.com/rockbenben/ChatGPT-Shortcut
- **Description Grounded**: True
- **LLM Enrichment Status**: DISABLED
- **Description Generation Method**: EXTRACTED_FROM_SOURCE

### 14. steel-browser
- **Description**: 🔥 Open Source Browser API for AI Agents & Apps. Steel Browser is a batteries-included browser sandbox that lets you automate the web without worrying about infrastructure.
- **LLM Provider Used**: NONE
- **Description Source Type**: GITHUB_REPOSITORY_DESCRIPTION
- **Description Source URL**: https://github.com/steel-dev/steel-browser
- **Description Grounded**: True
- **LLM Enrichment Status**: DISABLED
- **Description Generation Method**: EXTRACTED_FROM_SOURCE

### 15. modly
- **Description**: Desktop app to generate 3D models from images or prompt using local AI — runs entirely on your GPU
- **LLM Provider Used**: NONE
- **Description Source Type**: GITHUB_REPOSITORY_DESCRIPTION
- **Description Source URL**: https://github.com/lightningpixel/modly
- **Description Grounded**: True
- **LLM Enrichment Status**: DISABLED
- **Description Generation Method**: EXTRACTED_FROM_SOURCE

### 16. autoclip
- **Description**: AutoClip : AI-powered video clipping and highlight generation · 一款智能高光提取与剪辑的二创工具
- **LLM Provider Used**: NONE
- **Description Source Type**: GITHUB_REPOSITORY_DESCRIPTION
- **Description Source URL**: https://github.com/zhouxiaoka/autoclip
- **Description Grounded**: True
- **LLM Enrichment Status**: DISABLED
- **Description Generation Method**: EXTRACTED_FROM_SOURCE

### 17. FunClip
- **Description**: FunASR-powered video transcription, subtitle generation, and LLM-assisted clipping tool with a local Gradio UI.
- **LLM Provider Used**: NONE
- **Description Source Type**: GITHUB_REPOSITORY_DESCRIPTION
- **Description Source URL**: https://github.com/modelscope/FunClip
- **Description Grounded**: True
- **LLM Enrichment Status**: DISABLED
- **Description Generation Method**: EXTRACTED_FROM_SOURCE

### 18. quotio
- **Description**: Stop juggling AI accounts. Quotio is a beautiful native macOS menu bar app that unifies your Claude, Gemini, OpenAI, Qwen, and Antigravity subscriptions – with real-time quota tracking and smart auto-failover for AI coding tools like Claude Code, OpenCode, and Droid.
- **LLM Provider Used**: NONE
- **Description Source Type**: GITHUB_REPOSITORY_DESCRIPTION
- **Description Source URL**: https://github.com/nguyenphutrong/quotio
- **Description Grounded**: True
- **LLM Enrichment Status**: DISABLED
- **Description Generation Method**: EXTRACTED_FROM_SOURCE

### 19. poster-design
- **Description**: 迅排设计 - 图片编辑器、AI 在线海报设计,仿稿定设计,适用于多种场景:海报生成、电商产品图、文章长图、视频/公众号封面等。A beautiful online image designer, suitable for various scenarios like generate posters, making design easier!
- **LLM Provider Used**: NONE
- **Description Source Type**: GITHUB_REPOSITORY_DESCRIPTION
- **Description Source URL**: https://github.com/palxiao/poster-design
- **Description Grounded**: True
- **LLM Enrichment Status**: DISABLED
- **Description Generation Method**: EXTRACTED_FROM_SOURCE

### 20. logfire
- **Description**: AI observability platform for production LLM and agent systems.
- **LLM Provider Used**: NONE
- **Description Source Type**: GITHUB_REPOSITORY_DESCRIPTION
- **Description Source URL**: https://github.com/pydantic/logfire
- **Description Grounded**: True
- **LLM Enrichment Status**: DISABLED
- **Description Generation Method**: EXTRACTED_FROM_SOURCE

### 21. judge0
- **Description**: Robust, fast, scalable, and sandboxed open-source online code execution system for humans and AI.
- **LLM Provider Used**: NONE
- **Description Source Type**: GITHUB_REPOSITORY_DESCRIPTION
- **Description Source URL**: https://github.com/judge0/judge0
- **Description Grounded**: True
- **LLM Enrichment Status**: DISABLED
- **Description Generation Method**: EXTRACTED_FROM_SOURCE

### 22. claude-devtools
- **Description**: The missing DevTools for Claude Code — inspect session logs, tool calls, token usage, subagents, and context window in a visual UI. Free, open source.
- **LLM Provider Used**: NONE
- **Description Source Type**: GITHUB_REPOSITORY_DESCRIPTION
- **Description Source URL**: https://github.com/matt1398/claude-devtools
- **Description Grounded**: True
- **LLM Enrichment Status**: DISABLED
- **Description Generation Method**: EXTRACTED_FROM_SOURCE

### 23. tutti
- **Description**: Where people and agents build in tune.
- **LLM Provider Used**: NONE
- **Description Source Type**: GITHUB_REPOSITORY_DESCRIPTION
- **Description Source URL**: https://github.com/tutti-os/tutti
- **Description Grounded**: True
- **LLM Enrichment Status**: DISABLED
- **Description Generation Method**: EXTRACTED_FROM_SOURCE

### 24. pinme
- **Description**: Deploy Your Frontend in a Single Command. Claude Code Skills supported.
- **LLM Provider Used**: NONE
- **Description Source Type**: GITHUB_REPOSITORY_DESCRIPTION
- **Description Source URL**: https://github.com/glitternetwork/pinme
- **Description Grounded**: True
- **LLM Enrichment Status**: DISABLED
- **Description Generation Method**: EXTRACTED_FROM_SOURCE

### 25. anything-analyzer
- **Description**: 全能协议分析工具:浏览器抓包 + MITM 代理 + 指纹伪装 + AI 分析 + MCP Server 无缝对接 AI Agent/IDE | All-in-one protocol analysis toolkit — built-in browser capture, MITM proxy, JS hooks, fingerprint spoofing, AI analysis & MCP server for agent integration
- **LLM Provider Used**: NONE
- **Description Source Type**: GITHUB_REPOSITORY_DESCRIPTION
- **Description Source URL**: https://github.com/Mouseww/anything-analyzer
- **Description Grounded**: True
- **LLM Enrichment Status**: DISABLED
- **Description Generation Method**: EXTRACTED_FROM_SOURCE

### 26. llm-wiki-agent
- **Description**: A personal knowledge base that builds and maintains itself. Drop in sources — Claude (or Codex/Gemini) reads them, extracts knowledge, and maintains a persistent interlinked wiki. Works with Claude Code, Codex, OpenCode, Gemini CLI. No API key needed.
- **LLM Provider Used**: NONE
- **Description Source Type**: GITHUB_REPOSITORY_DESCRIPTION
- **Description Source URL**: https://github.com/SamurAIGPT/llm-wiki-agent
- **Description Grounded**: True
- **LLM Enrichment Status**: DISABLED
- **Description Generation Method**: EXTRACTED_FROM_SOURCE

### 27. VulnClaw
- **Description**: 基于 AI Agent + MCP 工具链 + 渗透 Skill 编排, 配合大语言模型, 自然语言输入 → 自动完成「信息收集 → 漏洞发现 → 漏洞利用 → 报告生成」全流程。
- **LLM Provider Used**: NONE
- **Description Source Type**: GITHUB_REPOSITORY_DESCRIPTION
- **Description Source URL**: https://github.com/Netw0rkNoob/VulnClaw
- **Description Grounded**: True
- **LLM Enrichment Status**: DISABLED
- **Description Generation Method**: EXTRACTED_FROM_SOURCE

### 28. any-auto-register
- **Description**: Auto-register & manage accounts for ChatGPT, Cursor, Kiro, Grok, Windsurf, Trae & 13+ AI platforms · Protocol/browser dual-mode · Plugin-based · One-click Mac/Windows desktop app
- **LLM Provider Used**: NONE
- **Description Source Type**: GITHUB_REPOSITORY_DESCRIPTION
- **Description Source URL**: https://github.com/lxf746/any-auto-register
- **Description Grounded**: True
- **LLM Enrichment Status**: DISABLED
- **Description Generation Method**: EXTRACTED_FROM_SOURCE

### 29. claude-tap
- **Description**: Intercept and inspect Coding Agent API traffic from Claude Code, Codex CLI, Gemini CLI, Cursor CLI, OpenCode, Kimi/Kimi Code, Pi, and Hermes in a local trace viewer.
- **LLM Provider Used**: NONE
- **Description Source Type**: GITHUB_REPOSITORY_DESCRIPTION
- **Description Source URL**: https://github.com/liaohch3/claude-tap
- **Description Grounded**: True
- **LLM Enrichment Status**: DISABLED
- **Description Generation Method**: EXTRACTED_FROM_SOURCE

### 30. open-terminal
- **Description**: A computer you can curl ⚡
- **LLM Provider Used**: NONE
- **Description Source Type**: GITHUB_REPOSITORY_DESCRIPTION
- **Description Source URL**: https://github.com/open-webui/open-terminal
- **Description Grounded**: True
- **LLM Enrichment Status**: DISABLED
- **Description Generation Method**: EXTRACTED_FROM_SOURCE

### 31. tuicr
- **Description**: a code review TUI with vim keybindings
- **LLM Provider Used**: NONE
- **Description Source Type**: GITHUB_REPOSITORY_DESCRIPTION
- **Description Source URL**: https://github.com/agavra/tuicr
- **Description Grounded**: True
- **LLM Enrichment Status**: DISABLED
- **Description Generation Method**: EXTRACTED_FROM_SOURCE

### 32. humanize-text
- **Description**: Open-source text humanization pipeline with every intermediate step published. Two LLM rewrites at temp 1.3, then two hops across different NMT engines. Four documented methodologies you can read, modify, and run locally.
- **LLM Provider Used**: NONE
- **Description Source Type**: GITHUB_REPOSITORY_DESCRIPTION
- **Description Source URL**: https://github.com/lynote-ai/humanize-text
- **Description Grounded**: True
- **LLM Enrichment Status**: DISABLED
- **Description Generation Method**: EXTRACTED_FROM_SOURCE

### 33. daily-arXiv-ai-enhanced
- **Description**: Automatically crawl arXiv papers daily and summarize them using AI. Illustrating them using GitHub Pages.
- **LLM Provider Used**: NONE
- **Description Source Type**: GITHUB_REPOSITORY_DESCRIPTION
- **Description Source URL**: https://github.com/dw-dengwei/daily-arXiv-ai-enhanced
- **Description Grounded**: True
- **LLM Enrichment Status**: DISABLED
- **Description Generation Method**: EXTRACTED_FROM_SOURCE

### 34. clawpanel
- **Description**: 🦞 OpenClaw & Hermes Agent 多引擎 AI 管理面板 — 内置 AI 助手(工具调用 + 图片识别 + 多模态),一键安装 | Tauri v2 跨平台桌面应用 | 11 种语言
- **LLM Provider Used**: NONE
- **Description Source Type**: GITHUB_REPOSITORY_DESCRIPTION
- **Description Source URL**: https://github.com/qingchencloud/clawpanel
- **Description Grounded**: True
- **LLM Enrichment Status**: DISABLED
- **Description Generation Method**: EXTRACTED_FROM_SOURCE

### 35. designer-skills
- **Description**: Designer Skills Collection: agentic skills, commands, and plugins for design — from research to systems, UI, interaction, and delivery.
- **LLM Provider Used**: NONE
- **Description Source Type**: GITHUB_REPOSITORY_DESCRIPTION
- **Description Source URL**: https://github.com/Owl-Listener/designer-skills
- **Description Grounded**: True
- **LLM Enrichment Status**: DISABLED
- **Description Generation Method**: EXTRACTED_FROM_SOURCE

### 36. oh-my-hermes
- **Description**: All in one plugin for Hermes Agent ⚚ the coding intelligence, a long-term memory system and model optimized workflow packages
- **LLM Provider Used**: NONE
- **Description Source Type**: GITHUB_REPOSITORY_DESCRIPTION
- **Description Source URL**: https://github.com/rlaope/oh-my-hermes
- **Description Grounded**: True
- **LLM Enrichment Status**: DISABLED
- **Description Generation Method**: EXTRACTED_FROM_SOURCE

### 37. Data-Analysis-Agent
- **Description**: 🚀你的私人数据分析助手。通过对话式交互,自动生成可视化报表与商业洞察,让数据决策变得像聊天一样简单。 🚀 Your personal data analysis assistant. Say goodbye to complex SQL and Excel formulas. An LLM-powered data analysis agent. Chat with your data to instantly generate visualizations and business insights. Making data-driven decisions has never been easier.
- **LLM Provider Used**: NONE
- **Description Source Type**: GITHUB_REPOSITORY_DESCRIPTION
- **Description Source URL**: https://github.com/Zafer-Liu/Data-Analysis-Agent
- **Description Grounded**: True
- **LLM Enrichment Status**: DISABLED
- **Description Generation Method**: EXTRACTED_FROM_SOURCE

### 38. lanhu-mcp
- **Description**: ⚡ 需求分析效率提升 200%!全球首个为 AI 编程时代设计的团队协作 MCP 服务器,自动分析需求自动编写前后端代码,下载切图
- **LLM Provider Used**: NONE
- **Description Source Type**: GITHUB_REPOSITORY_DESCRIPTION
- **Description Source URL**: https://github.com/dsphper/lanhu-mcp
- **Description Grounded**: True
- **LLM Enrichment Status**: DISABLED
- **Description Generation Method**: EXTRACTED_FROM_SOURCE

### 39. token-monitor
- **Description**: Local-first desktop widget for tracking token usage, costs, and limits across 37+ AI coding tools—including Claude Code, Codex, Cursor, OpenCode, and OpenClaw—with multi-device sync.
- **LLM Provider Used**: NONE
- **Description Source Type**: GITHUB_REPOSITORY_DESCRIPTION
- **Description Source URL**: https://github.com/Javis603/token-monitor
- **Description Grounded**: True
- **LLM Enrichment Status**: DISABLED
- **Description Generation Method**: EXTRACTED_FROM_SOURCE

### 40. open-cowork
- **Description**: Open-source AI agent desktop app for Windows & macOS. One-click install Claude Code, MCP tools, and Skills — with sandbox isolation, multi-model support, and Feishu/Slack integration.
- **LLM Provider Used**: NONE
- **Description Source Type**: GITHUB_REPOSITORY_DESCRIPTION
- **Description Source URL**: https://github.com/OpenCoworkAI/open-cowork
- **Description Grounded**: True
- **LLM Enrichment Status**: DISABLED
- **Description Generation Method**: EXTRACTED_FROM_SOURCE

### 41. stealth-browser-mcp
- **Description**: The only browser automation that bypasses anti-bot systems. AI writes network hooks, clones UIs pixel-perfect via simple chat.
- **LLM Provider Used**: NONE
- **Description Source Type**: GITHUB_REPOSITORY_DESCRIPTION
- **Description Source URL**: https://github.com/vibheksoni/stealth-browser-mcp
- **Description Grounded**: True
- **LLM Enrichment Status**: DISABLED
- **Description Generation Method**: EXTRACTED_FROM_SOURCE

### 42. LiveAgent
- **Description**: A fully functional AI Agent desktop client that supports Webui access and can be creatively customized and expanded!
- **LLM Provider Used**: NONE
- **Description Source Type**: GITHUB_REPOSITORY_DESCRIPTION
- **Description Source URL**: https://github.com/Stack-Cairn/LiveAgent
- **Description Grounded**: True
- **LLM Enrichment Status**: DISABLED
- **Description Generation Method**: EXTRACTED_FROM_SOURCE

### 43. opc-skills
- **Description**: Agent Skills for Solopreneurs
- **LLM Provider Used**: NONE
- **Description Source Type**: GITHUB_REPOSITORY_DESCRIPTION
- **Description Source URL**: https://github.com/ReScienceLab/opc-skills
- **Description Grounded**: True
- **LLM Enrichment Status**: DISABLED
- **Description Generation Method**: EXTRACTED_FROM_SOURCE

### 44. VoiceMem
- **Description**: Infrastructure for the next generation of voice agents, designed to provide universal memory. It is divided into a left brain and a right brain, storing information and emotions respectively, while a fully streaming architecture eliminates latency at the fundamental level.
- **LLM Provider Used**: NONE
- **Description Source Type**: GITHUB_REPOSITORY_DESCRIPTION
- **Description Source URL**: https://github.com/xzf-thu/VoiceMem
- **Description Grounded**: True
- **LLM Enrichment Status**: DISABLED
- **Description Generation Method**: EXTRACTED_FROM_SOURCE

### 45. Seal-Report
- **Description**: Database Reporting Tool and Tasks (.Net)
- **LLM Provider Used**: NONE
- **Description Source Type**: GITHUB_REPOSITORY_DESCRIPTION
- **Description Source URL**: https://github.com/ariacom/Seal-Report
- **Description Grounded**: True
- **LLM Enrichment Status**: DISABLED
- **Description Generation Method**: EXTRACTED_FROM_SOURCE

### 46. TokenTracker
- **Description**: Local-first AI token usage & cost tracker for 31 coding tools incl. Claude Code, Codex, Cursor, Gemini & DeepSeek Harness—with native apps. Never reads prompts.
- **LLM Provider Used**: NONE
- **Description Source Type**: GITHUB_REPOSITORY_DESCRIPTION
- **Description Source URL**: https://github.com/xiufengsun/TokenTracker
- **Description Grounded**: True
- **LLM Enrichment Status**: DISABLED
- **Description Generation Method**: EXTRACTED_FROM_SOURCE

### 47. sprite-gen
- **Description**: Generate clean 2D game sprites & animation atlases — component-row pipeline: state rows, alpha cleanup, frame extraction, runtime atlases. Codex/Claude skill.
- **LLM Provider Used**: NONE
- **Description Source Type**: GITHUB_REPOSITORY_DESCRIPTION
- **Description Source URL**: https://github.com/aldegad/sprite-gen
- **Description Grounded**: True
- **LLM Enrichment Status**: DISABLED
- **Description Generation Method**: EXTRACTED_FROM_SOURCE

### 48. gortex
- **Description**: High-performance code-intelligence engine for AI agents and IDE, supports 257 languages, multi repositories, based on graph, with access via CLI, MCP Server, and API. AI coding agents teammate - expose only needed information, cutting token usage up to 50x. 100% local. Discord: https://discord.gg/39MFHu3J5d
- **LLM Provider Used**: NONE
- **Description Source Type**: GITHUB_REPOSITORY_DESCRIPTION
- **Description Source URL**: https://github.com/zzet/gortex
- **Description Grounded**: True
- **LLM Enrichment Status**: DISABLED
- **Description Generation Method**: EXTRACTED_FROM_SOURCE

### 49. openilink-hub
- **Description**: 开源微信 Bot 管理平台 + App 应用市场 | Self-hosted WeChat Bot Platform with App Marketplace | Lark · Slack · Discord · DingTalk · GitHub · Notion · 20+ Apps | AI Tools | 7 Language SDKs
- **LLM Provider Used**: NONE
- **Description Source Type**: GITHUB_REPOSITORY_DESCRIPTION
- **Description Source URL**: https://github.com/openilink/openilink-hub
- **Description Grounded**: True
- **LLM Enrichment Status**: DISABLED
- **Description Generation Method**: EXTRACTED_FROM_SOURCE

### 50. Atomic-Chat
- **Description**: Local AI app and inference engine for agents. Run open-weight LLMs locally — private, 100% offline on your computer. Join our Discord: https://discord.com/invite/8wGSsvmg4V
- **LLM Provider Used**: NONE
- **Description Source Type**: GITHUB_REPOSITORY_DESCRIPTION
- **Description Source URL**: https://github.com/AtomicBot-ai/Atomic-Chat
- **Description Grounded**: True
- **LLM Enrichment Status**: DISABLED
- **Description Generation Method**: EXTRACTED_FROM_SOURCE

## Semantic Audit Audit Trail & Verification Directives
- **Curriculum & Non-Tool Filtering**: Repositories matching academy, course, tutorial, papers, or benchmark patterns are strictly excluded from accepted records.
- **Website vs Repository Verification**: `website_verified` is strictly `False` unless a standalone external official domain is present and accessible.
- **Logo Verification Semantics**: GitHub `og:image` social previews are retained for preview display but marked `logo_verified = False`.
- **Grounding Hierarchy**: Slogan-only descriptions ('runs anywhere', etc.) are replaced with substantive initial paragraphs extracted from official README documentation.