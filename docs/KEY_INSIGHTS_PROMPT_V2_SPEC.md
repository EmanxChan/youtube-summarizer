# Key Insights Prompt Enhancement V2 - Specification

**Issue:** Current insights are generic and surface-level  
**Goal:** Generate deeper, more nuanced insights with strategic context  
**Status:** 📋 Spec - Awaiting Approval

---

## Problem Analysis

### Current Output Example (AI Coding Video):

1. "Planning with AI is more efficient than jumping straight to coding for complex features."
2. "Parallel research operations with specialized agents can gather knowledge faster than human planning."
3. "Eight research strategies help an AI learn patterns and preferences in a codebase."
4. "Using a combination of these strategies allows an AI to make decisions based on context, taste, and judgment."
5. "Continually refining and expanding the AI's knowledge base improves its performance over time."

### Why These Are Too Generic:

❌ **Obvious truisms** - #5: "refining improves performance" (no insight here)  
❌ **Just states facts** - #3: "Eight strategies help" (so what? why does this matter?)  
❌ **Lacks nuance** - #1: Doesn't explain tradeoffs or when NOT to plan  
❌ **No depth** - #4: Surface-level statement without underlying principles  
❌ **Too broad** - Could apply to any topic, not memorable or specific  

---

## What's Missing: Depth Markers

Real insights should include:

1. **Underlying mechanisms** - Explain HOW/WHY something works at a deeper level
2. **Tradeoffs & limitations** - What are the costs? When does it break down?
3. **Non-obvious implications** - What surprising consequences follow?
4. **Mental models** - What framework helps understand this?
5. **Context & boundaries** - When does this apply vs. not apply?
6. **Counterintuitive elements** - What seems wrong but is actually right?

---

## Proposed Enhanced Prompt V2

```python
prompt = f"""You are a world-class analyst who extracts profound, non-obvious insights from educational content. Your insights reveal deeper patterns, tradeoffs, and strategic implications that most people miss.

Title: {video_title}
Content: {transcript}

Generate exactly {count} insights that capture the deepest concepts, principles, and strategic implications from this content.

CRITICAL REQUIREMENTS - Each insight MUST:

1. **Reveal underlying mechanisms** - Explain WHY something works at a fundamental level, not just WHAT happens
2. **Include tradeoffs or limitations** - Show the costs, constraints, or boundaries (nothing is universally good)
3. **Provide non-obvious implications** - Surface surprising consequences or counterintuitive aspects
4. **Use specific examples** - Reference concrete situations or scenarios from the content
5. **Be memorable and distinctive** - Should stick in someone's mind, not be generic
6. **Show strategic context** - Explain when/where this matters and when it doesn't

LENGTH: 30-40 words per insight (2-3 sentences)

AVOID AT ALL COSTS:
- Generic truisms ("X improves Y", "Using Z helps achieve better results")
- Obvious statements anyone would know
- Action verbs (Learn, Master, Implement, Use)
- Vague platitudes without specifics
- Surface-level descriptions

QUALITY TEST:
Ask yourself: "Would an expert in this field find this insight valuable, or would they say 'obviously'?"
Only include insights that pass this test.

EXAMPLES OF EXCELLENT INSIGHTS:

BAD (Generic):
"Planning with AI is more efficient than jumping straight to coding for complex features."

GOOD (Insightful):
"AI code assistants front-load cognitive work—requiring extensive upfront context through research strategies—because they lack the implicit codebase understanding developers build through daily immersion, creating a fundamental inversion where setup investment determines long-term leverage rather than immediate productivity."

---

BAD (Generic):
"Eight research strategies help an AI learn patterns and preferences in a codebase."

GOOD (Insightful):
"Multiple research strategies exist because no single approach captures both explicit patterns (what the code does) and implicit taste (how the team prefers to do it), requiring AI systems to triangulate understanding through complementary lenses much like anthropologists studying a culture through multiple methodologies."

---

BAD (Generic):
"Continually refining and expanding the AI's knowledge base improves its performance over time."

GOOD (Insightful):
"AI code assistants demonstrate a compound learning curve where initial context-gathering creates diminishing returns on individual queries but exponential improvements in decision quality over time, inverting the typical tool learning curve where early investment yields immediate payoff."

---

Now generate {count} insights that match this EXCELLENT quality standard. Each insight should be profound enough that an expert would pause and think "I hadn't considered it that way."

Return ONLY the {count} insights, one per line, without numbers or bullet points."""
```

---

## Key Changes from V1 to V2

| Aspect | V1 (Current) | V2 (Proposed) |
|--------|--------------|---------------|
| **Length** | 25-35 words | 30-40 words (allow more depth) |
| **Demand** | "Be meaningful" | "Pass expert test - would they say 'obviously'?" |
| **Specificity** | General guidance | Must include tradeoffs, mechanisms, implications |
| **Examples** | 3 good examples | 3 BAD vs GOOD pairs showing contrast |
| **Strictness** | Suggestions | "CRITICAL REQUIREMENTS", "AVOID AT ALL COSTS" |
| **Quality bar** | Conceptual vs action | "Profound", "non-obvious", "expert-worthy" |

---

## Example Transformations

### Topic: AI Code Assistants

**CURRENT OUTPUT (Generic):**
> "Eight research strategies help an AI learn patterns and preferences in a codebase."

**V2 EXPECTED (Insightful):**
> "Multiple research strategies exist because no single approach captures both explicit patterns (what the code does) and implicit taste (how the team prefers to do it), requiring AI systems to triangulate understanding through complementary lenses much like anthropologists studying a culture through multiple methodologies."

**What makes V2 better:**
- ✅ Explains WHY multiple strategies (not just states that they exist)
- ✅ Shows the dichotomy: explicit vs implicit knowledge
- ✅ Uses analogy (anthropology) to aid understanding
- ✅ Reveals deeper principle about knowledge acquisition

---

### Topic: Docker

**CURRENT OUTPUT (Generic):**
> "Container layer caching dramatically reduces build times by reusing unchanged dependencies."

**V2 EXPECTED (Insightful):**
> "Layer caching transforms Docker's value proposition from deployment consistency to development velocity by exploiting dependency stability—most builds change code frequently but libraries rarely—creating asymmetric time savings where 10% of changes eliminate 90% of rebuild time, though this benefit inverts when dependency churn is high."

**What makes V2 better:**
- ✅ Explains the underlying principle (dependency stability)
- ✅ Shows the tradeoff (fails when dependencies change often)
- ✅ Quantifies impact (10% changes = 90% savings)
- ✅ Reveals when it works vs. doesn't work

---

### Topic: Sleep Science (Huberman Lab)

**CURRENT OUTPUT (Generic):**
> "Sleep operates on multiple biological timescales creating compound effects on cognitive function."

**V2 EXPECTED (Insightful):**
> "Sleep architecture reveals a non-linear relationship with performance where 6 hours of sleep isn't 75% as good as 8 hours—it's more like 40%—because REM and deep sleep concentrate in different cycle positions, meaning partial sleep selectively starves specific brain functions while appearing to maintain alertness, creating a dangerous illusion of adequacy."

**What makes V2 better:**
- ✅ Reveals non-intuitive math (not linear)
- ✅ Explains mechanism (REM/deep sleep concentration)
- ✅ Shows dangerous implication (illusion of adequacy)
- ✅ Specific enough to be actionable

---

## Testing Criteria

An insight passes quality check if it answers YES to:

1. **Would an expert find this valuable?** (not "obviously")
2. **Does it explain underlying mechanisms?** (not just what happens)
3. **Does it show tradeoffs or limits?** (not universally positive)
4. **Is it specific to this content?** (couldn't apply to everything)
5. **Would someone remember this?** (distinctive, not generic)
6. **Does it change how you think?** (new mental model or perspective)

---

## Potential Model Limitation

**Important consideration:** Mistral (via Ollama) may not be sophisticated enough to generate truly insightful content consistently.

**Testing plan:**
1. Deploy V2 prompt with Ollama/Mistral
2. Test with 3-5 examples
3. If still generic, test with OpenAI GPT-4o-mini or GPT-4
4. Compare output quality

**Hypothesis:** GPT-4 will produce significantly better insights than Mistral for this task because it requires:
- Deeper reasoning
- Nuanced understanding
- Counterintuitive thinking
- Strategic analysis

---

## Alternative: Hybrid Approach

If Mistral continues to produce generic insights, consider:

**Option A: Use GPT-4 for insights only**
- Summary: Mistral (faster, cheaper)
- Key Insights: GPT-4 (higher quality)
- Next Steps: Mistral (simpler task)

**Option B: Provide more context**
- Give AI the summary first
- Ask for insights based on summary + transcript
- More context might help Mistral understand what's important

**Option C: Multi-pass refinement**
- First pass: Generate insights
- Second pass: "Make these more insightful by adding tradeoffs and mechanisms"
- Doubles API calls but might improve quality

---

## Implementation Plan

### Step 1: Update Prompt
- Replace current prompt in `ai_summarizer.py` (lines 161-194)
- Use V2 prompt with stricter requirements
- Increase length to 30-40 words

### Step 2: Test with Current Model (Ollama/Mistral)
- Test with 3 diverse examples:
  1. Technical tutorial (Docker, React)
  2. Podcast (The Daily, Huberman Lab)
  3. Educational (Coding, Science)

### Step 3: Evaluate Quality
- Check if insights pass 6 quality criteria
- If still generic → proceed to Step 4

### Step 4: Test with Better Model (if needed)
- Add option to use GPT-4 specifically for insights
- Compare Mistral vs GPT-4 output quality
- Make recommendation based on results

### Step 5: Deploy Best Approach
- Use best model/prompt combination
- Document any model-specific settings

---

## Recommendation

🔴 **Try V2 prompt first**, but **be prepared to switch models** if Mistral can't handle the cognitive demand.

**Reasoning:**
- Mistral is great for summarization (pattern matching, extraction)
- Insight generation requires deeper reasoning, nuance, strategic thinking
- GPT-4 significantly outperforms on complex reasoning tasks
- Small cost increase (insights only) worth quality improvement

---

## Questions for User

1. **Should we try V2 prompt with Mistral first?** (free, but might still be generic)
2. **Or switch to GPT-4 for insights only?** (small cost, likely much better)
3. **What's more important: cost or insight quality?**

---

## Estimated Impact

### If V2 Prompt Works with Mistral:
- ✅ Significantly better insights (50-70% improvement)
- ✅ Zero additional cost
- ✅ Same speed

### If Need to Switch to GPT-4:
- ✅ Excellent insight quality (90%+ improvement)
- ⚠️ Small cost increase (~$0.01-0.02 per summary)
- ⚠️ Slight speed decrease (API latency)

---

## Status

📋 **Awaiting User Decision:**

**Option 1:** Try V2 prompt with Mistral  
**Option 2:** Switch to GPT-4 for insights  
**Option 3:** Try V2 with Mistral, fall back to GPT-4 if generic  

Which approach would you like?
