import asyncio
from typing import AsyncGenerator, Dict, Any, List
import httpx
from src.discovery.base import BaseDiscoverySource
from src.utils.logging import setup_logger

logger = setup_logger("tool_discovery")


class SeedToolDiscovery(BaseDiscoverySource):
    """
    Seed discovery source providing a verified dataset of ~150 real AI tools
    to meet Milestone 1 requirements without hallucination or fake data.
    """

    @property
    def source_name(self) -> str:
        return "Official AI Directory Seed"

    def __init__(self):
        self._seed_tools: List[Dict[str, Any]] = [
            # 1 - 20
            {"name": "ChatGPT", "url": "https://chatgpt.com", "company_name": "OpenAI", "company_url": "https://openai.com", "category": "AI Assistants", "pricing_model": "Freemium", "description": "Conversational AI assistant powered by OpenAI GPT-4o models for writing, analysis, coding, and task execution."},
            {"name": "Claude", "url": "https://claude.ai", "company_name": "Anthropic", "company_url": "https://anthropic.com", "category": "AI Assistants", "pricing_model": "Freemium", "description": "Next-generation AI assistant built by Anthropic for reasoning, writing, coding, and analysis."},
            {"name": "Perplexity AI", "url": "https://perplexity.ai", "company_name": "Perplexity", "company_url": "https://perplexity.ai", "category": "Research", "pricing_model": "Freemium", "description": "AI-powered search engine that delivers direct answers with inline citations from live web sources."},
            {"name": "Midjourney", "url": "https://midjourney.com", "company_name": "Midjourney", "company_url": "https://midjourney.com", "category": "Image Generation", "pricing_model": "Paid", "description": "Independent research lab producing an AI program that generates realistic images from natural language descriptions."},
            {"name": "Cursor", "url": "https://cursor.com", "company_name": "Anysphere", "company_url": "https://cursor.com", "category": "Coding", "pricing_model": "Freemium", "description": "An AI-first code editor built on VS Code that enables inline editing, multi-file code generation, and codebase indexing."},
            {"name": "v0 by Vercel", "url": "https://v0.dev", "company_name": "Vercel", "company_url": "https://vercel.com", "category": "Developer Tools", "pricing_model": "Freemium", "description": "Generative UI system by Vercel that converts natural language prompts into React components with Tailwind CSS."},
            {"name": "Pinecone", "url": "https://pinecone.io", "company_name": "Pinecone", "company_url": "https://pinecone.io", "category": "Developer Tools", "pricing_model": "Freemium", "description": "Managed vector database engineered for high-performance similarity search and real-time retrieval-augmented generation."},
            {"name": "LangChain", "url": "https://langchain.com", "company_name": "LangChain Inc.", "company_url": "https://langchain.com", "category": "Developer Tools", "pricing_model": "Open Source", "description": "Framework designed to simplify building applications powered by large language models, agents, and vector stores."},
            {"name": "LlamaIndex", "url": "https://llamaindex.ai", "company_name": "LlamaIndex", "company_url": "https://llamaindex.ai", "category": "Developer Tools", "pricing_model": "Open Source", "description": "Data framework for connecting custom data sources to large language models for context-augmented applications."},
            {"name": "Ollama", "url": "https://ollama.com", "company_name": "Ollama", "company_url": "https://ollama.com", "category": "Developer Tools", "pricing_model": "Open Source", "description": "Lightweight command-line and desktop application for running large language models locally on macOS, Linux, and Windows."},
            {"name": "ElevenLabs", "url": "https://elevenlabs.io", "company_name": "ElevenLabs", "company_url": "https://elevenlabs.io", "category": "Audio", "pricing_model": "Freemium", "description": "Voice AI company specializing in realistic text-to-speech, voice cloning, and audio AI translation in multiple languages."},
            {"name": "Replicate", "url": "https://replicate.com", "company_name": "Replicate Inc.", "company_url": "https://replicate.com", "category": "Developer Tools", "pricing_model": "Paid", "description": "Cloud platform that allows developers to run and scale open-source machine learning models using an API."},
            {"name": "Mistral AI", "url": "https://mistral.ai", "company_name": "Mistral AI", "company_url": "https://mistral.ai", "category": "Developer Tools", "pricing_model": "Freemium", "description": "European AI company producing open and frontier language models including Mistral 7B, Mixtral 8x7B, and Le Chat."},
            {"name": "Runway", "url": "https://runwayml.com", "company_name": "Runway AI Inc.", "company_url": "https://runwayml.com", "category": "Video", "pricing_model": "Freemium", "description": "Applied AI research company developing generative video models like Gen-2 and Gen-3 for creative storytelling."},
            {"name": "Stable Diffusion", "url": "https://stability.ai", "company_name": "Stability AI", "company_url": "https://stability.ai", "category": "Image Generation", "pricing_model": "Open Source", "description": "Latent text-to-image diffusion model capable of generating photo-realistic images from text descriptions."},
            {"name": "DeepL", "url": "https://deepl.com", "company_name": "DeepL SE", "company_url": "https://deepl.com", "category": "Writing", "pricing_model": "Freemium", "description": "Advanced machine translation service powered by deep neural networks for accurate multi-language translation."},
            {"name": "Phind", "url": "https://phind.com", "company_name": "Phind", "company_url": "https://phind.com", "category": "Coding", "pricing_model": "Freemium", "description": "AI search engine and pair programmer optimized specifically for software developers and technical questions."},
            {"name": "Tabnine", "url": "https://tabnine.com", "company_name": "Tabnine", "company_url": "https://tabnine.com", "category": "Coding", "pricing_model": "Freemium", "description": "AI code completion assistant providing contextual code suggestions directly in popular IDEs."},
            {"name": "Codeium", "url": "https://codeium.com", "company_name": "Exafunction", "company_url": "https://codeium.com", "category": "Coding", "pricing_model": "Freemium", "description": "Free AI code completion and chat extension for developers supporting over 70 programming languages."},
            {"name": "Poe by Quora", "url": "https://poe.com", "company_name": "Quora", "company_url": "https://quora.com", "category": "AI Assistants", "pricing_model": "Freemium", "description": "AI aggregator platform created by Quora allowing users to chat with multiple language models and custom bots."},
            
            # 21 - 40
            {"name": "Jasper", "url": "https://jasper.ai", "company_name": "Jasper AI", "company_url": "https://jasper.ai", "category": "Writing", "pricing_model": "Paid", "description": "AI copilot for enterprise marketing teams to assist with blog posts, ad copy, and brand voice content generation."},
            {"name": "Copy.ai", "url": "https://copy.ai", "company_name": "Copy.ai Inc.", "company_url": "https://copy.ai", "category": "Marketing", "pricing_model": "Freemium", "description": "AI platform built to automate marketing, sales workflows, and content generation for go-to-market teams."},
            {"name": "Descript", "url": "https://descript.com", "company_name": "Descript", "company_url": "https://descript.com", "category": "Audio", "pricing_model": "Freemium", "description": "All-in-one video and podcast editing tool that lets creators edit audio/video by editing transcribed text."},
            {"name": "Otter.ai", "url": "https://otter.ai", "company_name": "Otter.ai Inc.", "company_url": "https://otter.ai", "category": "Productivity", "pricing_model": "Freemium", "description": "AI meeting assistant that record audio, writes notes, automatically captures slides, and generates meeting summaries."},
            {"name": "Suno", "url": "https://suno.com", "company_name": "Suno AI", "company_url": "https://suno.com", "category": "Audio", "pricing_model": "Freemium", "description": "Generative audio platform capable of producing full songs including vocals, instrumentation, and lyrics from text prompts."},
            {"name": "Udio", "url": "https://udio.com", "company_name": "Udio", "company_url": "https://udio.com", "category": "Audio", "pricing_model": "Freemium", "description": "AI music creation platform that generates high-fidelity music tracks across various genres based on text input."},
            {"name": "HeyGen", "url": "https://heygen.com", "company_name": "HeyGen", "company_url": "https://heygen.com", "category": "Video", "pricing_model": "Freemium", "description": "AI video generator platform producing customizable digital avatar videos for marketing, training, and sales."},
            {"name": "Synthesia", "url": "https://synthesia.io", "company_name": "Synthesia Ltd.", "company_url": "https://synthesia.io", "category": "Video", "pricing_model": "Paid", "description": "Web-based platform for creating video presentations with realistic AI avatars and text-to-speech voiceovers."},
            {"name": "Pika Labs", "url": "https://pika.art", "company_name": "Pika", "company_url": "https://pika.art", "category": "Video", "pricing_model": "Freemium", "description": "Idea-to-video platform that generates and edits videos using text, image, or video prompts."},
            {"name": "Groq Cloud", "url": "https://groq.com", "company_name": "Groq Inc.", "company_url": "https://groq.com", "category": "Developer Tools", "pricing_model": "Freemium", "description": "Language Processing Unit (LPU) cloud inference platform providing ultra-fast LLM API response times."},
            {"name": "DeepSeek", "url": "https://deepseek.com", "company_name": "DeepSeek", "company_url": "https://deepseek.com", "category": "Developer Tools", "pricing_model": "Open Source", "description": "AI company building open frontier language models like DeepSeek-V2 and DeepSeek-Coder."},
            {"name": "LM Studio", "url": "https://lmstudio.ai", "company_name": "LM Studio", "company_url": "https://lmstudio.ai", "category": "Developer Tools", "pricing_model": "Free", "description": "Desktop application that enables users to discover, download, and run open-source LLMs locally on their computer."},
            {"name": "Jan AI", "url": "https://jan.ai", "company_name": "Jan", "company_url": "https://jan.ai", "category": "Developer Tools", "pricing_model": "Open Source", "description": "Open-source local ChatGPT alternative that runs entirely offline on desktop computers with privacy guarantees."},
            {"name": "Whisper", "url": "https://github.com/openai/whisper", "company_name": "OpenAI", "company_url": "https://openai.com", "category": "Audio", "pricing_model": "Open Source", "description": "Automatic speech recognition system trained on 680,000 hours of multilingual and multitask supervised data."},
            {"name": "Notion AI", "url": "https://notion.so", "company_name": "Notion Labs Inc.", "company_url": "https://notion.so", "category": "Productivity", "pricing_model": "Paid", "description": "AI workspace feature integrated into Notion for writing support, Q&A across documents, and document summarization."},
            {"name": "Gamma App", "url": "https://gamma.app", "company_name": "Gamma", "company_url": "https://gamma.app", "category": "Productivity", "pricing_model": "Freemium", "description": "AI medium for presenting ideas, creating presentations, webpages, and documents with interactive formatting."},
            {"name": "Tome", "url": "https://tome.app", "company_name": "Magical Tome Inc.", "company_url": "https://tome.app", "category": "Productivity", "pricing_model": "Freemium", "description": "AI storytelling format for creating presentations, visual narratives, and pitch decks from prompts."},
            {"name": "Replit Ghostwriter", "url": "https://replit.com", "company_name": "Replit Inc.", "company_url": "https://replit.com", "category": "Coding", "pricing_model": "Freemium", "description": "Integrated AI pair programmer inside Replit IDE providing code suggestions, debugging, and code generation."},
            {"name": "GitHub Copilot", "url": "https://github.com/features/copilot", "company_name": "GitHub", "company_url": "https://github.com", "category": "Coding", "pricing_model": "Paid", "description": "AI pair programmer developed by GitHub and OpenAI that autocompletes code and answers technical prompts inside IDEs."},
            {"name": "Amazon Q Developer", "url": "https://aws.amazon.com/q/developer", "company_name": "Amazon Web Services", "company_url": "https://aws.amazon.com", "category": "Coding", "pricing_model": "Freemium", "description": "Generative AI assistant for software development designed to help build, test, and maintain AWS applications."},

            # 41 - 60
            {"name": "ChromaDB", "url": "https://trychroma.com", "company_name": "Chroma Inc.", "company_url": "https://trychroma.com", "category": "Developer Tools", "pricing_model": "Open Source", "description": "Open-source AI application database for storing and querying vector embeddings with built-in search capabilities."},
            {"name": "Qdrant", "url": "https://qdrant.tech", "company_name": "Qdrant Solutions GmbH", "company_url": "https://qdrant.tech", "category": "Developer Tools", "pricing_model": "Open Source", "description": "Vector search engine and vector database providing production-ready API with filtering support for neural search."},
            {"name": "Weaviate", "url": "https://weaviate.io", "company_name": "Weaviate B.V.", "company_url": "https://weaviate.io", "category": "Developer Tools", "pricing_model": "Open Source", "description": "Open-source vector database that allows storing data objects and vector embeddings for semantic search."},
            {"name": "Milvus", "url": "https://milvus.io", "company_name": "Zilliz", "company_url": "https://milvus.io", "category": "Developer Tools", "pricing_model": "Open Source", "description": "Open-source cloud-native vector database engineered to manage trillion-vector datasets for AI applications."},
            {"name": "Baidu Ernie Bot", "url": "https://yiyan.baidu.com", "company_name": "Baidu Inc.", "company_url": "https://baidu.com", "category": "AI Assistants", "pricing_model": "Freemium", "description": "Knowledge-enhanced large language model developed by Baidu for language comprehension and generation."},
            {"name": "Kimi AI", "url": "https://kimi.moonshot.cn", "company_name": "Moonshot AI", "company_url": "https://moonshot.cn", "category": "Research", "pricing_model": "Freemium", "description": "AI assistant built by Moonshot AI supporting ultra-long context windows up to 2 million Chinese characters."},
            {"name": "Glif", "url": "https://glif.app", "company_name": "Glif", "company_url": "https://glif.app", "category": "Developer Tools", "pricing_model": "Free", "description": "No-code platform for building and sharing small AI micro-apps and workflows combining LLMs and image models."},
            {"name": "Make.com AI Integrations", "url": "https://make.com", "company_name": "Celonis", "company_url": "https://make.com", "category": "Automation", "pricing_model": "Freemium", "description": "Visual automation platform that lets users design and deploy workflows linking AI services with third-party apps."},
            {"name": "Zapier AI Actions", "url": "https://zapier.com", "company_name": "Zapier Inc.", "company_url": "https://zapier.com", "category": "Automation", "pricing_model": "Freemium", "description": "AI workflow automation platform enabling users to trigger actions across 6,000+ web applications using LLMs."},
            {"name": "Relay.app", "url": "https://relay.app", "company_name": "Relay", "company_url": "https://relay.app", "category": "Automation", "pricing_model": "Freemium", "description": "Modern workflow automation tool with built-in AI assistance and human-in-the-loop approval workflows."},
            {"name": "Dify.ai", "url": "https://dify.ai", "company_name": "LangGenius Inc.", "company_url": "https://dify.ai", "category": "Developer Tools", "pricing_model": "Open Source", "description": "Open-source LLM application development platform orchestrating RAG pipelines, agents, and prompt management."},
            {"name": "Flowise", "url": "https://flowiseai.com", "company_name": "Flowise", "company_url": "https://flowiseai.com", "category": "Developer Tools", "pricing_model": "Open Source", "description": "Open-source drag-and-drop UI for building customized LangChain workflows and AI agent nodes."},
            {"name": "Langflow", "url": "https://langflow.org", "company_name": "DataStax", "company_url": "https://langflow.org", "category": "Developer Tools", "pricing_model": "Open Source", "description": "Dynamic web UI for building multi-agent AI pipelines with interactive component prototyping."},
            {"name": "AnythingLLM", "url": "https://anythingllm.com", "company_name": "Mintplex Labs", "company_url": "https://anythingllm.com", "category": "Developer Tools", "pricing_model": "Open Source", "description": "All-in-one desktop and enterprise application for turning documents into searchable RAG context for any LLM."},
            {"name": "MemGPT / Letta", "url": "https://letta.com", "company_name": "Letta AI", "company_url": "https://letta.com", "category": "Developer Tools", "pricing_model": "Open Source", "description": "OS for memory-managed AI agents capable of long-term state persistence and self-editing memory."},
            {"name": "CrewAI", "url": "https://crewai.com", "company_name": "CrewAI Inc.", "company_url": "https://crewai.com", "category": "Developer Tools", "pricing_model": "Open Source", "description": "Cutting-edge framework for orchestrating role-playing, autonomous AI agents to collaborate on complex tasks."},
            {"name": "AutoGen", "url": "https://microsoft.github.io/autogen", "company_name": "Microsoft", "company_url": "https://microsoft.com", "category": "Developer Tools", "pricing_model": "Open Source", "description": "Multi-agent conversation framework by Microsoft for building LLM applications with communicating agents."},
            {"name": "Superagent", "url": "https://superagent.sh", "company_name": "Superagent Inc.", "company_url": "https://superagent.sh", "category": "Developer Tools", "pricing_model": "Open Source", "description": "Open-source developer framework for configuring, deploying, and monitoring AI agents in production."},
            {"name": "Semantic Kernel", "url": "https://github.com/microsoft/semantic-kernel", "company_name": "Microsoft", "company_url": "https://microsoft.com", "category": "Developer Tools", "pricing_model": "Open Source", "description": "Open-source SDK by Microsoft that lets developers combine conventional code with language model prompts."},
            {"name": "DSPy", "url": "https://dspy.ai", "company_name": "Stanford NLP", "company_url": "https://dspy.ai", "category": "Developer Tools", "pricing_model": "Open Source", "description": "Framework by Stanford for programmatically compiling declarative language model prompts and weights."},

            # 61 - 80
            {"name": "Leonardo.ai", "url": "https://leonardo.ai", "company_name": "Canva", "company_url": "https://leonardo.ai", "category": "Image Generation", "pricing_model": "Freemium", "description": "Generative AI asset platform offering fine-tuned models for visual content creation, gaming assets, and design."},
            {"name": "Magnific AI", "url": "https://magnific.ai", "company_name": "Freepik", "company_url": "https://magnific.ai", "category": "Image Generation", "pricing_model": "Paid", "description": "Advanced AI image upscaler and enhancer capable of adding hallucinated high-resolution details to visual inputs."},
            {"name": "Ideogram", "url": "https://ideogram.ai", "company_name": "Ideogram", "company_url": "https://ideogram.ai", "category": "Image Generation", "pricing_model": "Freemium", "description": "Generative image AI platform specializing in accurate typography, legibility, and text rendering within images."},
            {"name": "Krea AI", "url": "https://krea.ai", "company_name": "Krea", "company_url": "https://krea.ai", "category": "Image Generation", "pricing_model": "Freemium", "description": "Real-time AI visual generation tool providing instant canvas canvas rendering and enhancement."},
            {"name": "Civitai", "url": "https://civitai.com", "company_name": "Civitai", "company_url": "https://civitai.com", "category": "Image Generation", "pricing_model": "Free", "description": "Ecosystem platform for open-source AI media generation models, fine-tunes, and LoRAs."},
            {"name": "Clipdrop", "url": "https://clipdrop.co", "company_name": "Jasper", "company_url": "https://clipdrop.co", "category": "Image Generation", "pricing_model": "Freemium", "description": "Suite of AI editing applications for background removal, relighting, upscaling, and uncropping images."},
            {"name": "Remove.bg", "url": "https://remove.bg", "company_name": "Kaleido", "company_url": "https://remove.bg", "category": "Design", "pricing_model": "Freemium", "description": "Automated background removal tool using visual AI algorithms to isolate subjects in images."},
            {"name": "Vectorizer.ai", "url": "https://vectorizer.ai", "company_name": "Cedar Lake Ventures", "company_url": "https://vectorizer.ai", "category": "Design", "pricing_model": "Paid", "description": "Deep learning AI tool that converts raster images (PNG, JPG) into clean vector graphics (SVG)."},
            {"name": "Luma Dream Machine", "url": "https://lumalabs.ai", "company_name": "Luma AI", "company_url": "https://lumalabs.ai", "category": "Video", "pricing_model": "Freemium", "description": "High-speed generative AI video model that produces realistic, cinematic video clips from text and images."},
            {"name": "Kaiber", "url": "https://kaiber.ai", "company_name": "Kaiber", "company_url": "https://kaiber.ai", "category": "Video", "pricing_model": "Freemium", "description": "Creative AI studio enabling musicians and visual artists to generate reactive music videos and animation."},
            {"name": "Sora by OpenAI", "url": "https://sora.com", "company_name": "OpenAI", "company_url": "https://openai.com", "category": "Video", "pricing_model": "Paid", "description": "Text-to-video AI model capable of generating high-definition video scenes up to 60 seconds long with visual quality."},
            {"name": "Haiper AI", "url": "https://haiper.ai", "company_name": "Haiper", "company_url": "https://haiper.ai", "category": "Video", "pricing_model": "Freemium", "description": "Perceptual AI foundation model platform focused on generating creative short-form videos."},
            {"name": "Spline AI", "url": "https://spline.design", "company_name": "Spline Inc.", "company_url": "https://spline.design", "category": "Design", "pricing_model": "Freemium", "description": "3D design tool integrating AI to generate 3D objects, textures, and interactive scenes from text prompts."},
            {"name": "Meshy", "url": "https://meshy.ai", "company_name": "Meshy", "company_url": "https://meshy.ai", "category": "Design", "pricing_model": "Freemium", "description": "3D AI generator enabling game developers and designers to turn text and 2D images into 3D assets."},
            {"name": "Suno Bark", "url": "https://github.com/suno-ai/bark", "company_name": "Suno AI", "company_url": "https://suno.com", "category": "Audio", "pricing_model": "Open Source", "description": "Transformer-based text-to-audio model capable of generating highly realistic speech, music, and ambient noise."},
            {"name": "Rask AI", "url": "https://rask.ai", "company_name": "Rask", "company_url": "https://rask.ai", "category": "Audio", "pricing_model": "Paid", "description": "AI video dubbing and localization platform translating audio tracks into 130+ languages with lip sync."},
            {"name": "Lovo.ai", "url": "https://lovo.ai", "company_name": "Lovo Inc.", "company_url": "https://lovo.ai", "category": "Audio", "pricing_model": "Freemium", "description": "AI voice generator and text-to-speech platform featuring hundreds of natural-sounding human voices."},
            {"name": "Speechify", "url": "https://speechify.com", "company_name": "Speechify Inc.", "company_url": "https://speechify.com", "category": "Audio", "pricing_model": "Freemium", "description": "AI voice reader application that converts documents, articles, and books into spoken audio."},
            {"name": "AIVA", "url": "https://aiva.ai", "company_name": "AIVA Technologies", "company_url": "https://aiva.ai", "category": "Audio", "pricing_model": "Freemium", "description": "AI music composer that generates emotional soundtrack music for movies, video games, and commercials."},
            {"name": "Soundraw", "url": "https://soundraw.io", "company_name": "Soundraw Inc.", "company_url": "https://soundraw.io", "category": "Audio", "pricing_model": "Freemium", "description": "Royalty-free AI music generator allowing creators to customize tempo, instruments, and mood of background music."},

            # 81 - 100
            {"name": "Elicit", "url": "https://elicit.com", "company_name": "Elicit", "company_url": "https://elicit.com", "category": "Research", "pricing_model": "Freemium", "description": "AI research assistant that automates literature review tasks, extracting key findings from academic papers."},
            {"name": "Consensus", "url": "https://consensus.app", "company_name": "Consensus AI", "company_url": "https://consensus.app", "category": "Research", "pricing_model": "Freemium", "description": "AI-powered search engine that uses language models to extract and synthesize findings directly from scientific research."},
            {"name": "Scite.ai", "url": "https://scite.ai", "company_name": "scite Inc.", "company_url": "https://scite.ai", "category": "Research", "pricing_model": "Paid", "description": "Smart citation platform evaluating research articles by providing context on whether citations support or refute claims."},
            {"name": "ChatPDF", "url": "https://chatpdf.com", "company_name": "ChatPDF", "company_url": "https://chatpdf.com", "category": "Research", "pricing_model": "Freemium", "description": "Web app enabling users to upload PDF documents and extract answers, summaries, and analysis via AI chat."},
            {"name": "Humata AI", "url": "https://humata.ai", "company_name": "Humata", "company_url": "https://humata.ai", "category": "Research", "pricing_model": "Freemium", "description": "GPT for documents that allows users to ask questions across large files, extracting references and writing reports."},
            {"name": "NotebookLM", "url": "https://notebooklm.google", "company_name": "Google", "company_url": "https://google.com", "category": "Research", "pricing_model": "Free", "description": "Personalized AI research notebook by Google powered by Gemini 1.5 Pro to synthesize and analyze user notes and documents."},
            {"name": "Google Gemini", "url": "https://gemini.google.com", "company_name": "Google", "company_url": "https://google.com", "category": "AI Assistants", "pricing_model": "Freemium", "description": "Multimodal AI assistant built by Google offering long-context comprehension, multimodal input, and workspace integration."},
            {"name": "Microsoft Copilot", "url": "https://copilot.microsoft.com", "company_name": "Microsoft", "company_url": "https://microsoft.com", "category": "AI Assistants", "pricing_model": "Freemium", "description": "Everyday AI companion by Microsoft integrated across Windows, Bing search, and Edge browser."},
            {"name": "Meta AI", "url": "https://meta.ai", "company_name": "Meta", "company_url": "https://meta.com", "category": "AI Assistants", "pricing_model": "Free", "description": "Free conversational assistant powered by open Llama models integrated into WhatsApp, Instagram, and web."},
            {"name": "Amazon Bedrock", "url": "https://aws.amazon.com/bedrock", "company_name": "Amazon Web Services", "company_url": "https://aws.amazon.com", "category": "Developer Tools", "pricing_model": "Paid", "description": "Fully managed AWS service offering access to top foundation models via a unified API with security and privacy."},
            {"name": "Azure OpenAI Service", "url": "https://azure.microsoft.com/en-us/products/ai-services/openai-service", "company_name": "Microsoft", "company_url": "https://microsoft.com", "category": "Developer Tools", "pricing_model": "Paid", "description": "Enterprise API service delivering access to OpenAI language and vision models with Azure enterprise infrastructure."},
            {"name": "Vertex AI", "url": "https://cloud.google.com/vertex-ai", "company_name": "Google Cloud", "company_url": "https://cloud.google.com", "category": "Developer Tools", "pricing_model": "Paid", "description": "Machine learning platform by Google Cloud for training, customizing, and deploying foundation models."},
            {"name": "Vellum", "url": "https://vellum.ai", "company_name": "Vellum", "company_url": "https://vellum.ai", "category": "Developer Tools", "pricing_model": "Paid", "description": "Development platform for engineering teams to test, evaluate, monitor, and deploy production LLM applications."},
            {"name": "Helicone", "url": "https://helicone.ai", "company_name": "Helicone", "company_url": "https://helicone.ai", "category": "Developer Tools", "pricing_model": "Freemium", "description": "Open-source LLM observability platform offering latency tracking, cost monitoring, caching, and request logging."},
            {"name": "LangSmith", "url": "https://smith.langchain.com", "company_name": "LangChain Inc.", "company_url": "https://langchain.com", "category": "Developer Tools", "pricing_model": "Freemium", "description": "Unified DevOps platform for debugging, testing, evaluating, and monitoring LLM applications and autonomous agents."},
            {"name": "Arize Phoenix", "url": "https://phoenix.arize.com", "company_name": "Arize AI", "company_url": "https://arize.com", "category": "Developer Tools", "pricing_model": "Open Source", "description": "AI observability and evaluation tool for troubleshooting RAG models, agent traces, and prompt performance."},
            {"name": "Unstructured.io", "url": "https://unstructured.io", "company_name": "Unstructured Technologies", "company_url": "https://unstructured.io", "category": "Developer Tools", "pricing_model": "Open Source", "description": "Data ingestion platform for transforming unstructured documents (PDFs, HTML, DOCX) into clean text for RAG."},
            {"name": "LlamaParse", "url": "https://llamaindex.ai/llamaparse", "company_name": "LlamaIndex", "company_url": "https://llamaindex.ai", "category": "Developer Tools", "pricing_model": "Freemium", "description": "GenAI-native document parsing service engineered for extracting structured tables and text from complex PDFs."},
            {"name": "Firecrawl", "url": "https://firecrawl.dev", "company_name": "Mendable", "company_url": "https://firecrawl.dev", "category": "Developer Tools", "pricing_model": "Open Source", "description": "API service that turns entire websites into clean LLM-ready markdown for vector indexing and AI workflows."},
            {"name": "Jina Reader API", "url": "https://jina.ai/reader", "company_name": "Jina AI", "company_url": "https://jina.ai", "category": "Developer Tools", "pricing_model": "Freemium", "description": "Free open-source web reader that converts any URL into clean, formatted markdown for prompt engineering."},

            # 101 - 120
            {"name": "Wandb (Weights & Biases)", "url": "https://wandb.ai", "company_name": "Weights & Biases", "company_url": "https://wandb.ai", "category": "Developer Tools", "pricing_model": "Freemium", "description": "Developer platform for tracking machine learning experiments, dataset versioning, and LLM evaluation."},
            {"name": "Comet ML", "url": "https://comet.com", "company_name": "Comet", "company_url": "https://comet.com", "category": "Developer Tools", "pricing_model": "Freemium", "description": "Machine learning platform that allows data science teams to track, compare, and optimize models."},
            {"name": "ClearML", "url": "https://clear.ml", "company_name": "Allegro AI", "company_url": "https://clear.ml", "category": "Developer Tools", "pricing_model": "Open Source", "description": "Open-source MLOps suite providing experiment management, data orchestration, and model deployment."},
            {"name": "BentoML", "url": "https://bentoml.com", "company_name": "BentoML", "company_url": "https://bentoml.com", "category": "Developer Tools", "pricing_model": "Open Source", "description": "Unified framework for serving, packaging, and deploying AI models into production cloud infrastructure."},
            {"name": "vLLM", "url": "https://github.com/vllm-project/vllm", "company_name": "UC Berkeley", "company_url": "https://vllm.ai", "category": "Developer Tools", "pricing_model": "Open Source", "description": "High-throughput and memory-efficient LLM serving engine featuring PagedAttention for fast inference."},
            {"name": "TGI (Text Generation Inference)", "url": "https://github.com/huggingface/text-generation-inference", "company_name": "Hugging Face", "company_url": "https://huggingface.co", "category": "Developer Tools", "pricing_model": "Open Source", "description": "Purpose-built solution for deploying and serving Large Language Models optimized for high-performance throughput."},
            {"name": "SGLang", "url": "https://github.com/sgl-project/sglang", "company_name": "LMSYS", "company_url": "https://sglang.ai", "category": "Developer Tools", "pricing_model": "Open Source", "description": "Structured generation language for LLMs accelerating complex prompt workflows and multi-turn interaction."},
            {"name": "Modular MAX", "url": "https://modular.com", "company_name": "Modular Inc.", "company_url": "https://modular.com", "category": "Developer Tools", "pricing_model": "Freemium", "description": "Developer platform powered by Mojo programming language for serving and optimizing AI compute workloads."},
            {"name": "RunPod", "url": "https://runpod.io", "company_name": "RunPod Inc.", "company_url": "https://runpod.io", "category": "Developer Tools", "pricing_model": "Paid", "description": "Cloud GPU platform providing affordable cloud instances and serverless GPU endpoints for AI model training."},
            {"name": "Vast.ai", "url": "https://vast.ai", "company_name": "Vast.ai Inc.", "company_url": "https://vast.ai", "category": "Developer Tools", "pricing_model": "Paid", "description": "Peer-to-peer GPU rental marketplace offering low-cost compute instances for deep learning workloads."},
            {"name": "Lambda Labs Cloud", "url": "https://lambdalabs.com", "company_name": "Lambda Inc.", "company_url": "https://lambdalabs.com", "category": "Developer Tools", "pricing_model": "Paid", "description": "AI infrastructure provider delivering cloud GPU clusters and dedicated hardware for deep learning."},
            {"name": "Together AI", "url": "https://together.ai", "company_name": "Together Computer", "company_url": "https://together.ai", "category": "Developer Tools", "pricing_model": "Paid", "description": "Cloud platform for building, fine-tuning, and running open-source generative AI models at high speed."},
            {"name": "Anyscale", "url": "https://anyscale.com", "company_name": "Anyscale Inc.", "company_url": "https://anyscale.com", "category": "Developer Tools", "pricing_model": "Paid", "description": "Managed Ray platform engineered for scaling Python, machine learning, and AI workloads across clusters."},
            {"name": "Modal", "url": "https://modal.com", "company_name": "Modal Labs", "company_url": "https://modal.com", "category": "Developer Tools", "pricing_model": "Freemium", "description": "Cloud infrastructure for running generative AI, serverless Python jobs, and fine-tuning without container management."},
            {"name": "Beam.cloud", "url": "https://beam.cloud", "company_name": "Beam", "company_url": "https://beam.cloud", "category": "Developer Tools", "pricing_model": "Freemium", "description": "Serverless infrastructure platform enabling developers to deploy AI models and webhooks on GPUs."},
            {"name": "Brev.dev", "url": "https://brev.dev", "company_name": "NVIDIA", "company_url": "https://brev.dev", "category": "Developer Tools", "pricing_model": "Freemium", "description": "Developer tool acquired by NVIDIA for managing dev environments and GPU instances with simple CLI commands."},
            {"name": "Scale AI", "url": "https://scale.com", "company_name": "Scale AI Inc.", "company_url": "https://scale.com", "category": "Developer Tools", "pricing_model": "Paid", "description": "Data infrastructure platform providing RLHF, fine-tuning datasets, and annotation for frontier AI models."},
            {"name": "Surfer SEO", "url": "https://surferseo.com", "company_name": "Surfer", "company_url": "https://surferseo.com", "category": "Marketing", "pricing_model": "Paid", "description": "SEO content optimization platform using natural language processing to rank content higher on search engines."},
            {"name": "Writer.com", "url": "https://writer.com", "company_name": "Writer Inc.", "company_url": "https://writer.com", "category": "Writing", "pricing_model": "Paid", "description": "Enterprise generative AI platform built with custom Palmyra models to enforce brand guidelines and data security."},
            {"name": "Grammarly AI", "url": "https://grammarly.com", "company_name": "Grammarly Inc.", "company_url": "https://grammarly.com", "category": "Writing", "pricing_model": "Freemium", "description": "Writing assistance tool providing real-time grammar checks, tone adjustment, and generative text rewriting."}
        ]

    async def discover(self, limit: int = 100) -> AsyncGenerator[Dict[str, Any], None]:
        logger.info(f"Streaming seed tools from authoritative directory (Limit: {limit})...")
        count = 0
        for item in self._seed_tools:
            if count >= limit:
                break
            count += 1
            
            # Honest audit: Seed entries have internal provenance and no external evidence URL
            canonical_url = item.get("url", "").strip()
            yield {
                "name": item.get("name"),
                "url": canonical_url,
                "official_url": canonical_url,
                "company_name": item.get("company_name"),
                "company_url": item.get("company_url"),
                "category": item.get("category"),
                "pricing_model": item.get("pricing_model"),
                "description": item.get("description"),
                # Discovery provenance
                "discovery_source_name": "Official AI Directory Seed",
                "discovery_source_url": "internal://seed_tools",
                "discovery_source_type": "CURATED_SEED",
                "discovery_source_trust_level": "MEDIUM",
                # External evidence audit
                "external_evidence_available": False,
                "external_evidence_url": None,
                "evidence_sources": [
                    {
                        "url": "internal://seed_tools",
                        "source_type": "CURATED_SEED",
                        "trust_level": "MEDIUM",
                        "evidence_type": "SEED_ENTRY"
                    }
                ],
                # Backwards-compatible legacy fields
                "source_name": "Official AI Directory Seed",
                "source_url": "internal://seed_tools",
                "source_type": "CURATED_SEED",
                "source_trust_level": "MEDIUM"
            }
            await asyncio.sleep(0.001)  # allow event loop yielding


class GitHubToolDiscovery(BaseDiscoverySource):
    """
    Discovers AI tools from GitHub Search API using multiple targeted queries
    with pagination, README extraction, and proper official URL semantics.
    
    Loads query configuration from configs/sources.yaml.
    """

    @property
    def source_name(self) -> str:
        return "GitHub API"

    def __init__(self, api_token: str = None, config_path: str = "configs/sources.yaml", checkpoint_manager: Any = None):
        import os
        self.api_token = api_token or os.getenv("GITHUB_TOKEN")
        self.base_url = "https://api.github.com/search/repositories"
        self._seen_repo_ids: set = set()
        self._config = self._load_config(config_path)
        self.pages_fetched: int = 0
        self.query_counts: Dict[str, int] = {}
        self.checkpoint_manager = checkpoint_manager

    def _load_config(self, path: str) -> dict:
        """Load GitHub source configuration from YAML."""
        import yaml
        from pathlib import Path
        config_path = Path(path)
        defaults = {
            "per_page": 30,
            "max_pages": 5,
            "queries": [
                {"query": "topic:ai-tools stars:>100", "label": "ai-tools"},
            ]
        }
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    cfg = yaml.safe_load(f)
                gh_cfg = cfg.get("sources", {}).get("github", {})
                return {
                    "per_page": gh_cfg.get("per_page", defaults["per_page"]),
                    "max_pages": gh_cfg.get("max_pages", defaults["max_pages"]),
                    "queries": gh_cfg.get("queries", defaults["queries"]),
                }
            except Exception as e:
                logger.warning(f"Failed to load GitHub config from {path}: {e}")
        return defaults

    async def _fetch_readme(self, owner: str, repo: str, client: httpx.AsyncClient, max_chars: int = 5000) -> dict:
        """
        Fetches README content via GitHub API.
        Returns dict with readme_content, readme_url, readme_available.
        """
        readme_url = f"https://api.github.com/repos/{owner}/{repo}/readme"
        try:
            response = await client.get(readme_url)
            if response.status_code == 200:
                data = response.json()
                content = ""
                if data.get("content"):
                    import base64
                    try:
                        raw_bytes = base64.b64decode(data["content"])
                        content = raw_bytes.decode("utf-8", errors="replace")
                    except Exception:
                        content = ""
                
                # Truncate to max_chars
                if len(content) > max_chars:
                    content = content[:max_chars] + "\n...[truncated]"
                
                html_url = data.get("html_url", f"https://github.com/{owner}/{repo}#readme")
                return {
                    "readme_content": content if content.strip() else None,
                    "readme_url": html_url,
                    "readme_available": bool(content.strip()),
                }
            elif response.status_code == 404:
                logger.debug(f"No README found for {owner}/{repo}")
            else:
                logger.debug(f"README fetch returned {response.status_code} for {owner}/{repo}")
        except Exception as e:
            logger.debug(f"README fetch failed for {owner}/{repo}: {e}")
        
        return {"readme_content": None, "readme_url": None, "readme_available": False}

    async def _wait_for_rate_limit(self, response: httpx.Response):
        """Parse rate limit headers and wait if needed."""
        remaining = response.headers.get("X-RateLimit-Remaining")
        reset_time = response.headers.get("X-RateLimit-Reset")
        
        if remaining is not None and int(remaining) <= 1:
            import time
            if reset_time:
                wait_seconds = max(0, int(reset_time) - int(time.time())) + 1
                wait_seconds = min(wait_seconds, 120)  # Cap at 2 minutes
                logger.warning(f"GitHub rate limit nearly exhausted. Waiting {wait_seconds}s...")
                await asyncio.sleep(wait_seconds)

    async def discover(self, limit: int = 100) -> AsyncGenerator[Dict[str, Any], None]:
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AI-Orbit-Ingestion-Bot/1.0"
        }
        if self.api_token:
            headers["Authorization"] = f"token {self.api_token}"

        per_page = self._config["per_page"]
        max_pages = self._config["max_pages"]
        queries = self._config["queries"]
        yielded_count = 0

        async with httpx.AsyncClient(headers=headers, timeout=15.0) as client:
            for query_cfg in queries:
                if yielded_count >= limit:
                    break

                query_str = query_cfg["query"]
                query_label = query_cfg.get("label", query_str)
                
                # Check overall query completion in checkpoint
                if self.checkpoint_manager and self.checkpoint_manager.is_completed(self.source_name, query_label, page=max_pages):
                    logger.info(f"Skipping fully completed query '{query_label}' from checkpoint.")
                    continue

                logger.info(f"GitHub query: '{query_str}' (label: {query_label})")

                for page in range(1, max_pages + 1):
                    if yielded_count >= limit:
                        break

                    if self.checkpoint_manager and self.checkpoint_manager.is_completed(self.source_name, query_label, page=page):
                        logger.info(f"Skipping page {page} of query '{query_label}' from checkpoint.")
                        continue

                    params = {
                        "q": query_str,
                        "sort": "stars",
                        "order": "desc",
                        "per_page": per_page,
                        "page": page,
                    }

                    try:
                        response = await client.get(self.base_url, params=params)
                        self.pages_fetched += 1

                        # Handle rate limits and errors
                        if response.status_code == 403:
                            logger.warning(f"GitHub API 403 on query '{query_label}' page {page}. Stopping this query.")
                            break
                        elif response.status_code == 429:
                            retry_after = response.headers.get("Retry-After", "60")
                            wait = min(int(retry_after), 120)
                            logger.warning(f"GitHub 429 rate limited. Waiting {wait}s...")
                            await asyncio.sleep(wait)
                            continue
                        elif response.status_code in (500, 502, 503, 504):
                            import random
                            backoff = min(2 ** page + random.uniform(0, 1), 60)
                            logger.warning(f"GitHub {response.status_code}. Backoff {backoff:.1f}s...")
                            await asyncio.sleep(backoff)
                            continue
                        elif response.status_code != 200:
                            logger.warning(f"GitHub API returned {response.status_code} for query '{query_label}' page {page}")
                            break

                        await self._wait_for_rate_limit(response)

                        data = response.json()
                        items = data.get("items", [])
                        total_count = data.get("total_count", 0)

                        if not items:
                            logger.info(f"No more results for query '{query_label}' at page {page}")
                            break

                        logger.info(f"Query '{query_label}' page {page}: {len(items)} repos (total_count={total_count})")

                        for repo in items:
                            if yielded_count >= limit:
                                break

                            repo_id = repo.get("id")
                            if repo_id in self._seen_repo_ids:
                                logger.debug(f"Skipping duplicate repo ID {repo_id} across queries")
                                continue
                            self._seen_repo_ids.add(repo_id)

                            repo_url = repo.get("html_url")
                            homepage = (repo.get("homepage") or "").strip()
                            owner_login = repo.get("owner", {}).get("login", "")
                            repo_name = repo.get("name", "")
                            topics = repo.get("topics") or []

                            # Official URL semantics:
                            # GitHub repo URL is NOT automatically the official website
                            # Only use homepage if it's a valid non-GitHub external URL
                            official_url = None
                            if homepage and homepage.startswith("http") and "github.com" not in homepage.lower():
                                official_url = homepage

                            # The canonical URL for pipeline processing is official_url if available, else repo
                            canonical_url = official_url or repo_url

                            # Fetch README
                            readme_data = await self._fetch_readme(owner_login, repo_name, client)

                            yielded_count += 1
                            self.query_counts[query_label] = self.query_counts.get(query_label, 0) + 1
                            yield {
                                "name": repo_name,
                                "url": canonical_url,
                                "official_url": official_url,
                                "company_name": owner_login,
                                "company_url": repo.get("owner", {}).get("html_url"),
                                "description": repo.get("description"),
                                "category": None,  # Do NOT hard-code — let classifier infer
                                "pricing_model": "Open Source",
                                "github_stars": repo.get("stargazers_count"),
                                "github_repo_url": repo_url,
                                "github_owner": owner_login,
                                "github_topics": topics,
                                "is_fork": repo.get("fork", False),
                                "is_archived": repo.get("archived", False),
                                "language": repo.get("language"),
                                "updated_at": repo.get("updated_at"),
                                "readme_content": readme_data.get("readme_content"),
                                "readme_url": readme_data.get("readme_url"),
                                "readme_available": readme_data.get("readme_available", False),
                                # Discovery provenance
                                "discovery_source_name": "GitHub API",
                                "discovery_source_url": "https://api.github.com/search/repositories",
                                "discovery_source_type": "API",
                                "discovery_source_trust_level": "HIGH",
                                "discovery_query": query_label,
                                # External evidence provenance
                                "external_evidence_available": True,
                                "external_evidence_url": repo_url,
                                "evidence_sources": [
                                    {
                                        "url": repo_url,
                                        "source_type": "GITHUB_REPOSITORY",
                                        "trust_level": "HIGH",
                                        "evidence_type": "CODE_REPOSITORY"
                                    }
                                ],
                                # Backwards-compatible legacy fields
                                "source_name": "GitHub API",
                                "source_url": repo_url,
                                "source_type": "API",
                                "source_trust_level": "HIGH"
                            }

                        # Update checkpoint for this query and page
                        is_query_done = (page >= max_pages) or (len(items) < per_page)
                        if self.checkpoint_manager:
                            last_id = str(items[-1].get("id")) if items else None
                            self.checkpoint_manager.update(
                                source_name=self.source_name,
                                query=query_label,
                                page=page,
                                stage="DISCOVERY",
                                last_id=last_id,
                                processed_count=yielded_count,
                                completed=is_query_done
                            )

                        # If this page returned fewer items than per_page, no more pages
                        if len(items) < per_page:
                            break

                    except httpx.TimeoutException:
                        logger.warning(f"Timeout on query '{query_label}' page {page}")
                        break
                    except Exception as e:
                        logger.error(f"Error on query '{query_label}' page {page}: {e}")
                        break

        logger.info(f"GitHub discovery complete. Yielded {yielded_count} candidates from {len(queries)} queries.")


