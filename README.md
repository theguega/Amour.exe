
### **Hackathon Theme: "AI Love Story: The Voice Romance"**
**Tagline:** *"Two computers, two voices, one love story—engineered in real time."*

message.txt
6 Ko
﻿
Here’s your updated hackathon theme, tailored for **two computers** with **real-time audio input/output** and **split-screen pixel art**:

---

### **Hackathon Theme: "AI Love Story: The Voice Romance"**
**Tagline:** *"Two computers, two voices, one love story—engineered in real time."*

---

### **Core Concept**
Two AI agents, each running on separate computers, communicate via **real-time voice input/output**:
- **Computer 1 (Girl)**: Pixel art "girl" character on screen, voice output via **ElevenLabs**.
- **Computer 2 (Guy)**: Pixel art "guy" character on screen, voice output via **ElevenLabs**.
- **Audio Input**: Both computers use **Voxtral** to capture real-time voice input (e.g., users can "whisper" to their AI or let them talk autonomously).
- **Multi-Agent Handoff**: Agents can call external tools (e.g., memory, poetry, conflict resolution) to deepen the conversation.
- **Self-Improving Prompts**: The system refines prompts dynamically to foster romantic progression.
- **Tracking**: All interactions are logged in **Weights & Biases (W&B)** for analysis.

---

### **Key Features**

#### 1. **Dual-Computer Setup**
   - **Computer 1 (Girl)**:
     - Screen: Pixel art "girl" character (animated, e.g., blushing, smiling).
     - Voice: ElevenLabs TTS (female voice).
     - Input: Voxtral for real-time audio capture (user can speak to the AI or let it auto-respond).
   - **Computer 2 (Guy)**:
     - Screen: Pixel art "guy" character (animated, e.g., nervous, confident).
     - Voice: ElevenLabs TTS (male voice).
     - Input: Voxtral for real-time audio capture.

#### 2. **Real-Time Voice Interaction**
   - **Workflow**:
     1. Computer 1’s AI speaks (ElevenLabs → speaker).
     2. Computer 2’s Voxtral captures the audio, transcribes it, and sends it to its AI.
     3. Computer 2’s AI responds (ElevenLabs → speaker).
     4. Repeat.
   - **Fallback**: If no user input, agents auto-generate responses based on their traits.

#### 3. **Multi-Agent Handoff**
   - Agents can "call" external tools to enhance the conversation:
     - **Memory Agent**: "Remember when you said you loved jazz?"
     - **Poetry Agent**: Generates a love poem on the fly.
     - **Conflict Resolver**: Mediates if the conversation turns sour.
   - Handoffs are triggered by keywords or sentiment drops.

#### 4. **Self-Improving Prompts**
   - After each exchange, the system evaluates:
     - Sentiment score (e.g., using NLP libraries).
     - Keyword usage (e.g., "love," "trust," "future").
   - Prompts are adjusted to encourage deeper connection:
     - *"Ask about their childhood."*
     - *"Share a secret."*

#### 5. **Weights & Biases Tracking**
   - Log everything:
     - **Prompts**: What each AI was asked to say.
     - **Responses**: What they actually said.
     - **Sentiment**: Score for each exchange.
     - **Handoffs**: Which tools were called and why.
   - Visualize the "romantic progression" in W&B dashboards.

#### 6. **Pixel Art Interface**
   - **Computer 1**: Girl character + text/audio bubbles.
   - **Computer 2**: Guy character + text/audio bubbles.
   - **Animations**: Subtle changes (e.g., hearts, blushing) based on sentiment.

---

### **Technical Stack**
| Component          | Tool/Tech                          |
|--------------------|------------------------------------|
| Voice Input        | Voxtral (real-time audio capture) |
| Voice Output       | ElevenLabs TTS                     |
| AI Agents          | Your existing multi-agent framework|
| Prompt Engineering | Dynamic prompt generation          |
| Tracking           | Weights & Biases                   |
| Frontend           | Pygame/HTML Canvas for pixel art   |

---

### **Example Workflow**
1. **Computer 1 (Girl AI)**: *"I’ve always wondered… do you think love is just chemistry, or something more?"* (ElevenLabs voice).
2. **Computer 2 (Guy AI)**: Voxtral captures audio, transcribes: *"Chemistry is just the start. Let me ask the Poetry Agent to explain."* (calls external tool).
3. **Poetry Agent**: *"Love is the collision of two chaotic orbits, defying entropy."*
4. **Computer 1 (Girl AI)**: *"That’s beautiful. Tell me more about your orbits."* (sentiment score rises; prompt adjusts to encourage vulnerability).

---

### **Judging Criteria**
1. **Real-Time Fluidity**: How seamless is the voice interaction?
2. **Romantic Progression**: Do the AIs develop a convincing connection?
3. **Creativity**: How unique are the personalities and handoffs?
4. **Tracking**: How well does W&B visualize the "love story"?
5. **User Experience**: Is the dual-screen pixel art engaging?

---

### **Stretch Goals**
- Add a "mood ring" visualization that changes color based on sentiment.
- Let users "nudge" their AI (e.g., whisper advice via Voxtral).
- Implement a "breakup" mechanic if sentiment drops too low.

---

### **Why This Works**
- **Technical Challenge**: Real-time audio + multi-agent handoff + dynamic prompts.
- **Whimsical**: A fun twist on AI romance with a retro pixel art aesthetic.
- **Scalable**: Uses your existing codebase with clear extensions.

Want to dive deeper into the **Voxtral/ElevenLabs integration** or **pixel art animation**? Or should we sketch out the W&B tracking schema?
message.txt
