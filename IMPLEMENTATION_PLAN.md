# Claude Changes - AI News Platform Implementation Plan
## Transforming DeepTutor into DeepTutorNews

---

## Executive Summary

Transform DeepTutor's educational platform into **DeepTutorNews** - an AI-powered news platform that aggregates news from reputable sources, provides fact-checking with RAG/web/paper search, generates automated insights, and offers deep research capabilities with minimalistic, modern UI.

**Timeline Complexity**: Large-scale architectural transformation
**Reusable Components**: ~60% of existing infrastructure
**New Components**: ~40% (news aggregation, fact-checking, image generation)

---

## Phase 1: Core Architecture Transformation

### 1.1 News Aggregation System (New Module)

**Component**: `src/agents/news_aggregator/`

**Agents**:
- `NewsScraperAgent`: Multi-source news collection
- `ContentParserAgent`: Extract article metadata (title, author, date, source)
- `DeduplicationAgent`: Identify duplicate stories across sources
- `CategoryAgent`: Auto-categorize news (politics, tech, health, etc.)

**Data Sources**:
- **News APIs**:
  - NewsAPI.org (70+ sources, 150k+ articles/day)
  - GNews API (60k+ sources worldwide)
  - The Guardian API (1.9M+ pieces of content)
- **RSS Feeds**: Custom curated list for reputable sources
- **Web Scraping**: Fallback for sources without APIs (using BeautifulSoup4 + Playwright)

**Storage**:
- New directory: `data/news/`
  - `raw/` - Original articles
  - `processed/` - Cleaned + categorized
  - `metadata.json` - Source credibility scores

**Integration Point**:
- Reuse existing `knowledge/document_loader.py` for processing
- Extend RAG system to handle news articles

**API Endpoints** (FastAPI):
```python
POST /api/news/fetch          # Trigger news aggregation
GET  /api/news/articles       # List articles (with filters)
GET  /api/news/article/{id}   # Get single article
GET  /api/news/sources        # List configured sources
```

---

### 1.2 Fact-Checking Engine (New Module)

**Component**: `src/agents/fact_checker/`

**Agents**:
- `ClaimExtractorAgent`: Identify verifiable claims in articles
- `EvidenceGatherAgent`: Use RAG + web search + paper search
- `VerificationAgent`: Cross-reference multiple sources
- `CredibilityScoreAgent`: Rate claim truthfulness (0-100)
- `BiasDetectorAgent`: Analyze political/ideological bias

**Multi-Source Verification Strategy**:
1. **RAG Search**: Query existing news knowledge base for similar claims
2. **Web Search**: Use Perplexity API for real-time fact-checking
3. **Paper Search**: Use ArXiv for scientific claims
4. **Cross-Reference**: Compare against fact-checking databases (Snopes API, FactCheck.org)

**Output Format**:
```json
{
  "claim": "...",
  "verdict": "true|false|misleading|unverifiable",
  "confidence": 0.85,
  "evidence": [
    {"source": "...", "url": "...", "relevance": 0.9}
  ],
  "bias_analysis": {
    "political_lean": "neutral",
    "emotional_tone": "balanced",
    "loaded_language": []
  }
}
```

**Reuse**:
- Existing `tools/web_search.py` (Perplexity)
- Existing `tools/paper_search_tool.py` (ArXiv)
- Existing `tools/rag_tool.py` (LightRAG for historical claims)

---

### 1.3 Deep Research for News (Adapt Existing)

**Component**: Adapt `src/agents/research/` for news analysis

**Modifications**:
- **RephraseAgent**: Convert news questions → research queries
- **DecomposeAgent**: Break down news stories into sub-topics
- **ResearchAgent**: Enhanced with news-specific prompts
- **NoteAgent**: Collect findings from multiple news sources
- **ReportingAgent**: Generate comprehensive news analysis reports

**New Presets** (add to `config/main.yaml`):
```yaml
research:
  presets:
    news_quick: {iteration: 3, max_topics: 5}
    news_deep: {iteration: 10, max_topics: 15}
    news_investigative: {iteration: 20, max_topics: 30}
```

**Use Cases**:
- Investigate developing stories
- Track evolving narratives
- Identify trend patterns
- Compare coverage across outlets

---

### 1.4 Automated Content Generation

**Component**: `src/agents/content_generator/`

**Agents**:
- `ArticleSynthesisAgent`: Generate news summaries from multiple sources
- `HeadlineGeneratorAgent`: Create engaging, unbiased headlines
- `ImageGenerationAgent`: **NEW** - Integrate DALL-E 3 / Stable Diffusion
- `VisualizationAgent`: Create charts (sentiment trends, topic evolution)

**Image Generation Strategy**:
```python
# Option A: OpenAI DALL-E 3
from openai import OpenAI
client.images.generate(
    model="dall-e-3",
    prompt="photorealistic news image: {article_summary}",
    size="1792x1024",
    quality="hd"
)

# Option B: Stability AI (for local hosting)
import requests
response = requests.post(
    "https://api.stability.ai/v2beta/stable-image/generate/core",
    headers={"authorization": f"Bearer {api_key}"},
    files={"prompt": prompt}
)
```

**Reuse**:
- Extend existing `src/agents/co_writer/` architecture
- Reuse markdown editing capabilities
- Add image storage: `data/news/generated_images/`

**API Endpoints**:
```python
POST /api/content/generate-article  # Auto-generate from sources
POST /api/content/generate-image    # Create article image
GET  /api/content/visualizations    # Trend charts
```

---

## Phase 2: Knowledge Graph & Trend Analysis

### 2.1 News Knowledge Graph

**Component**: Enhance existing LightRAG with news-specific entities

**Entity Types**:
- People (politicians, journalists, experts)
- Organizations (companies, governments, NGOs)
- Events (elections, disasters, announcements)
- Locations (countries, cities, regions)
- Topics (keywords, themes)

**Relationship Types**:
- `MENTIONS` - Article mentions entity
- `RELATED_TO` - Entities co-occur
- `CONTRADICTS` - Conflicting claims
- `CONFIRMS` - Supporting evidence
- `EVOLVES_FROM` - Story progression

**Visualization**:
- Reuse existing `cytoscape` integration (already in frontend)
- New component: `web/components/news/NewsGraphView.tsx`
- Interactive network showing entity relationships

**Storage**:
- Extend `data/knowledge_bases/news_graph/`
- Use LightRAG's graph storage backend

---

### 2.2 Trend Detection & Analysis

**Component**: `src/agents/trend_analyzer/`

**Agents**:
- `TrendDetectorAgent`: Identify emerging topics (using TF-IDF + time decay)
- `SentimentTrackerAgent`: Track sentiment over time
- `NoveltyEvaluatorAgent`: Detect genuinely new information vs. recycled content
- `PredictiveAgent`: Forecast topic importance (using time-series ML)

**Metrics**:
```python
{
  "topic": "AI regulation",
  "mention_count": 347,
  "growth_rate": "+125% (7 days)",
  "sentiment": {
    "positive": 0.32,
    "neutral": 0.45,
    "negative": 0.23
  },
  "novelty_score": 0.78,
  "predicted_trend": "rising"
}
```

**Visualization**:
- Time-series charts (using Chart.js or Recharts)
- Heatmaps for topic clustering
- Sentiment evolution graphs

---

## Phase 3: Frontend Redesign (Minimalistic + Modern)

### 3.1 Design System

**Framework**: Keep Next.js 14 + TailwindCSS

**Color Palette** (Modern & Professional):
```css
/* Primary Colors */
--primary: #2563eb      /* Blue - Trust & Authority */
--primary-dark: #1e40af
--primary-light: #60a5fa

/* Accent Colors */
--accent: #10b981       /* Green - Truth/Verified */
--warning: #f59e0b      /* Amber - Misleading */
--danger: #ef4444       /* Red - False */

/* Neutrals */
--bg-primary: #ffffff
--bg-secondary: #f9fafb
--bg-dark: #111827
--text-primary: #111827
--text-secondary: #6b7280

/* Glassmorphism */
--glass: rgba(255, 255, 255, 0.7)
--glass-dark: rgba(17, 24, 39, 0.8)
```

**Typography**:
- Headlines: `Inter` (clean, modern)
- Body: `Source Sans 3` (readable)
- Code/Data: `JetBrains Mono`

**Component Library**:
- Keep existing: `framer-motion`, `lucide-react`
- Add: `shadcn/ui` for consistent components
- Add: `recharts` for data visualization

---

### 3.2 New UI Components

**Landing Page** (`web/app/page.tsx`):
```
┌─────────────────────────────────────────┐
│  [Logo] DeepTutorNews     [🔍] Search   │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────────┐  ┌──────────────┐ │
│  │  Top Stories    │  │ Fact Check   │ │
│  │  [Cards...]     │  │ [Live Feed]  │ │
│  └─────────────────┘  └──────────────┘ │
│                                         │
│  ┌─────────────────────────────────────┐│
│  │  Trending Topics [Graph View]      ││
│  └─────────────────────────────────────┘│
└─────────────────────────────────────────┘
```

**Article View** (`web/app/article/[id]/page.tsx`):
- Hero image (generated or from source)
- Fact-check badges (✅ Verified, ⚠️ Misleading, ❌ False)
- Inline citations with hover previews
- Related articles sidebar
- Sentiment indicator
- Source credibility score

**Research Dashboard** (`web/app/research/page.tsx`):
- Query builder for deep research
- Real-time progress (reuse existing WebSocket)
- Interactive knowledge graph
- Export to PDF (reuse existing html2canvas + jspdf)

**Trend Analytics** (`web/app/trends/page.tsx`):
- Time-series charts
- Topic clusters
- Sentiment heatmaps
- Predictive forecasts

---

### 3.3 Navigation Redesign

**Main Menu**:
```
┌─────────────────────────────────────────┐
│ 🏠 Home                                 │
│ 📰 Latest News                          │
│ ✓  Fact Check                           │
│ 🔬 Deep Research                        │
│ 📈 Trends & Analytics                   │
│ 🎨 Idea Generator (for journalists)    │
│ 💡 Novel Insights                       │
│ 📚 Knowledge Base                       │
└─────────────────────────────────────────┘
```

**Responsive Design**:
- Mobile-first approach
- Collapsible sidebar
- Bottom navigation for mobile

---

## Phase 4: Backend API Updates

### 4.1 New API Routes

**News Module**:
```python
# src/api/routes/news.py
@router.post("/fetch")           # Aggregate news
@router.get("/articles")         # List with filters
@router.get("/article/{id}")     # Single article
@router.get("/sources")          # Configured sources
@router.post("/source/add")      # Add new source
```

**Fact-Checking**:
```python
# src/api/routes/fact_check.py
@router.post("/verify")          # Check claim
@router.get("/history")          # Past fact-checks
@router.websocket("/ws/verify")  # Real-time verification
```

**Trends**:
```python
# src/api/routes/trends.py
@router.get("/trending")         # Current trending topics
@router.get("/sentiment/{topic}") # Sentiment over time
@router.get("/predictions")      # Forecast trends
```

**Content Generation**:
```python
# src/api/routes/content.py
@router.post("/generate/article")
@router.post("/generate/image")
@router.post("/generate/visualization")
```

---

### 4.2 WebSocket Enhancements

**Real-Time News Feed**:
```python
@router.websocket("/ws/news/live")
async def news_stream(websocket: WebSocket):
    # Push new articles as they're aggregated
    # Push fact-check updates
    # Push breaking news alerts
```

**Research Progress**:
- Reuse existing `/ws/research` endpoint
- Adapt for news-specific research

---

## Phase 5: Configuration & Deployment

### 5.1 New Configuration Files

**`config/news.yaml`**:
```yaml
news:
  sources:
    newsapi:
      enabled: true
      api_key: ${NEWSAPI_KEY}
      country: us
      categories: [general, business, technology, science]

    guardian:
      enabled: true
      api_key: ${GUARDIAN_API_KEY}

    rss_feeds:
      - url: https://feeds.bbci.co.uk/news/rss.xml
        name: BBC News
        credibility_score: 0.95
      - url: https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml
        name: New York Times
        credibility_score: 0.93

  fact_check:
    min_confidence: 0.7
    max_sources_check: 10
    enable_bias_detection: true

  content_generation:
    image_model: dall-e-3  # or stable-diffusion
    auto_generate_summaries: true

  trend_analysis:
    time_window_days: 7
    min_mentions: 5
    novelty_threshold: 0.6
```

**`.env` additions**:
```bash
# News APIs
NEWSAPI_KEY=your_key
GUARDIAN_API_KEY=your_key
GNEWS_API_KEY=your_key

# Image Generation
DALLE_API_KEY=your_key
STABILITY_API_KEY=your_key

# Fact-Checking APIs
SNOPES_API_KEY=your_key
FACTCHECK_API_KEY=your_key
```

---

### 5.2 Database Considerations

**Current**: File-based JSON storage

**Recommendation**: Migrate to database for news platform scale

**Option A - PostgreSQL** (Recommended):
```yaml
# Benefits:
- Full-text search for articles
- JSONB for flexible metadata
- PostGIS for location-based news
- Time-series queries for trends

# Schema:
articles(id, title, content, source, published_at, category, metadata)
fact_checks(id, article_id, claim, verdict, confidence, evidence)
trends(id, topic, timestamp, mention_count, sentiment)
```

**Option B - Keep File-Based**:
- Use SQLite for lightweight querying
- Keep existing JSON for compatibility
- Add indexing for performance

**Decision Point**: Ask user for preference based on scale expectations

---

## Phase 6: Testing & Quality Assurance

### 6.1 Unit Tests

**New Test Files**:
- `tests/agents/test_news_aggregator.py`
- `tests/agents/test_fact_checker.py`
- `tests/agents/test_trend_analyzer.py`
- `tests/api/test_news_routes.py`
- `tests/tools/test_image_generation.py`

**Testing Strategy**:
- Mock API responses (NewsAPI, Guardian, etc.)
- Test fact-checking accuracy with known claims
- Validate trend detection algorithms
- Test image generation fallbacks

---

### 6.2 Integration Tests

**End-to-End Scenarios**:
1. Fetch news → Store → Display on frontend
2. Submit claim → Fact-check → Show results with evidence
3. Trigger research → Generate report → Visualize in graph
4. Detect trend → Track over time → Predict future

---

### 6.3 Performance Benchmarks

**Targets**:
- News aggregation: < 30s for 100 articles
- Fact-checking: < 10s per claim
- Research report: < 2min for quick preset
- Page load: < 2s (Lighthouse score > 90)

---

## Phase 7: Documentation Updates

### 7.1 User Documentation

**Update `docs/` (VitePress)**:
- Quick start guide for news platform
- How to add news sources
- Fact-checking tutorial
- Deep research for news stories
- Trend analysis guide

---

### 7.2 Developer Documentation

**API Documentation**:
- Auto-generate with FastAPI's `/docs` (Swagger)
- Add examples for each endpoint

**Agent Architecture**:
- Document new agents
- Flow diagrams for fact-checking pipeline
- Knowledge graph schema

---

## Implementation Roadmap

### Sprint 1: Foundation (Week 1-2)
- [ ] Set up news aggregation infrastructure
- [ ] Integrate NewsAPI + Guardian API
- [ ] Create news storage schema
- [ ] Basic frontend news list component

### Sprint 2: Fact-Checking Core (Week 3-4)
- [ ] Build ClaimExtractorAgent
- [ ] Implement multi-source verification
- [ ] Add credibility scoring
- [ ] Create fact-check UI components

### Sprint 3: Research & Analysis (Week 5-6)
- [ ] Adapt research module for news
- [ ] Build trend detection system
- [ ] Implement knowledge graph for news
- [ ] Add sentiment analysis

### Sprint 4: Content Generation (Week 7-8)
- [ ] Integrate image generation API
- [ ] Build article synthesis agent
- [ ] Create visualization tools
- [ ] Add automated insights

### Sprint 5: Frontend Redesign (Week 9-10)
- [ ] Implement new design system
- [ ] Build all major UI components
- [ ] Add interactive visualizations
- [ ] Mobile responsive design

### Sprint 6: Integration & Testing (Week 11-12)
- [ ] End-to-end testing
- [ ] Performance optimization
- [ ] Bug fixes
- [ ] Documentation

### Sprint 7: Deployment & Launch (Week 13-14)
- [ ] Production deployment setup
- [ ] Monitoring & logging
- [ ] User acceptance testing
- [ ] Launch! 🚀

---

## Key Architectural Decisions to Validate with User

### 1. Database Choice
**Question**: Do you expect high traffic/scale?
- **Option A**: PostgreSQL (recommended for production)
- **Option B**: Keep file-based (simpler, current architecture)

### 2. Image Generation Provider
**Question**: Preferred image generation approach?
- **Option A**: OpenAI DALL-E 3 (higher quality, $0.040-0.080 per image)
- **Option B**: Stability AI ($0.002-0.020 per image)
- **Option C**: Local Stable Diffusion (free, requires GPU)

### 3. News Sources Priority
**Question**: Which news sources are most important?
- Geographic focus (US, UK, Global)?
- Topic focus (General, Tech, Politics, Science)?
- Language support (English only, multilingual)?

### 4. Real-Time vs. Batch Processing
**Question**: How current should news be?
- **Option A**: Real-time streaming (every 5-15 min)
- **Option B**: Scheduled batches (hourly, daily)

### 5. Fact-Checking Depth
**Question**: Balance speed vs. thoroughness?
- **Option A**: Quick check (3-5 sources, < 10s)
- **Option B**: Deep verification (10+ sources, 30-60s)
- **Option C**: User-selectable presets

---

## Dependencies to Install

**Backend**:
```bash
pip install newsapi-python      # NewsAPI integration
pip install feedparser          # RSS feed parsing
pip install beautifulsoup4      # Web scraping
pip install playwright          # Dynamic content scraping
pip install transformers        # Sentiment analysis
pip install scikit-learn        # Trend detection (TF-IDF)
pip install openai>=1.0.0       # Image generation (DALL-E)
pip install stability-sdk       # Stability AI (if chosen)
pip install psycopg2-binary     # PostgreSQL (if chosen)
```

**Frontend**:
```bash
npm install @shadcn/ui          # UI components
npm install recharts            # Data visualization
npm install react-query         # Data fetching
npm install zustand             # State management
```

---

## Risk Mitigation

### Technical Risks

**Risk 1: News API Rate Limits**
- **Mitigation**: Implement caching layer, use multiple API providers

**Risk 2: Fact-Checking Accuracy**
- **Mitigation**: Multi-source verification, confidence scores, human review option

**Risk 3: Image Generation Costs**
- **Mitigation**: Cache generated images, use free tier initially, add user controls

**Risk 4: Performance at Scale**
- **Mitigation**: Implement pagination, lazy loading, database indexing

### User Experience Risks

**Risk 1: Information Overload**
- **Mitigation**: Smart filtering, personalization, clean UI

**Risk 2: Bias in AI Analysis**
- **Mitigation**: Transparent sourcing, multiple perspectives, bias indicators

---

## Success Metrics

**Platform Health**:
- Uptime: > 99.5%
- Page load: < 2s
- API response: < 500ms

**Content Quality**:
- Fact-check accuracy: > 85%
- Source diversity: > 20 reputable sources
- Duplicate detection: > 95%

**User Engagement**:
- Article views
- Research queries
- Fact-check requests
- Time on platform

---

## Future Enhancements (Post-Launch)

1. **Personalization**: User preference learning
2. **Multi-language Support**: Translate news + analysis
3. **Mobile Apps**: iOS + Android
4. **Browser Extension**: Fact-check any webpage
5. **API for Developers**: Public API access
6. **Community Features**: User comments, voting
7. **Newsletter Generation**: Daily digest emails
8. **Podcast Generation**: TTS news summaries (reuse existing TTS)

---

## Conclusion

This plan transforms DeepTutor into a comprehensive AI news platform while preserving 60% of the existing architecture. The modular approach allows incremental development and testing.

**Key Strengths**:
✅ Leverages existing RAG, research, and agent infrastructure
✅ Multi-source fact-checking with evidence
✅ Deep research capabilities for investigative journalism
✅ Automated content generation with AI
✅ Modern, minimalistic UI design
✅ Scalable architecture

**Next Steps**:
1. Review and approve this plan
2. Answer architectural decision questions
3. Begin Sprint 1 implementation
4. Iterate based on feedback

Let's build the future of AI-powered news! 🚀
