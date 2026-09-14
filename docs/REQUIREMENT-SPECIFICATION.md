# AI Call Center — Requirement Specification

**Document Status:** Draft for Review / Approval  
**Document Type:** Requirement Specification (RS)  
**Target Repository:** `Ittipolint/AI-Call-Center`  
**Version:** 0.1  
**Date:** 2026-09-14  
**Language:** Thai (with technical terms in English)

---

## 1. Purpose and Scope

ระบบ **AI Call Center** เป็น Web-based application ที่ใช้ AI เป็นผู้สนทนากับผู้ติดต่อผ่านเสียง โดย AI สามารถเปลี่ยน “บทบาทหน้าที่” (AI Role) ตาม `System Message` ที่ผู้ดูแลกำหนด และใช้ข้อมูลจาก **RAG Knowledge Base** เป็นแหล่งอ้างอิงในการสนทนา ตอบคำถาม และเก็บข้อมูลอย่างมีหลักฐาน โดยมีเป้าหมายหลักคือ:

1. รับข้อมูลจากเสียงพูดหรือไฟล์เสียง
2. สนทนาโต้ตอบอย่างสุภาพและเป็นธรรมชาติ
3. ดึงข้อมูลที่จำเป็นจากผู้ติดต่อให้ได้มากที่สุด
4. แปลงข้อมูลจากบทสนทนาเป็นข้อมูลแบบ Structured Data เพื่อกรอกลงแบบฟอร์ม
5. แสดง Transcript ของการสนทนาแบบต่อเนื่อง
6. อนุญาตให้ Admin/Authorized User เปลี่ยน AI Role และ Knowledge Base โดยไม่ต้องแก้ source code
7. รองรับการขยายจาก 1 concurrent caller ไปสู่หลาย concurrent callers
8. ทำงานทั้งหมดบน Docker และเข้าถึงจาก Internet ผ่าน Cloudflare Free

เอกสารฉบับนี้กำหนด **Functional Requirements, Non-Functional Requirements, Data Requirements, AI/RAG Requirements, Security Requirements, Acceptance Criteria และข้อจำกัดของระบบ** เพื่อใช้เป็น baseline ก่อนจัดทำ Technical Specification (TS)

---

# 2. System Vision

ระบบแบ่งความสามารถหลักออกเป็น 7 บริการเชิงหน้าที่:

- **Conversation / Call Session**
- **Speech-to-Text (STT)**
- **AI Orchestrator / LLM**
- **Text-to-Speech (TTS)**
- **Dynamic Form / CMS**
- **RAG Knowledge Base**
- **Dashboard & Reporting**

แนวคิดสำคัญคือ **AI Role และ Form Schema ต้องเป็น configuration-driven** ไม่ผูกติดกับ code เพื่อให้สามารถเปลี่ยน use case เช่น Complaint Center, Customer Service, Help Desk, HR, Survey หรือ Government Hotline ได้โดยไม่ต้องสร้างระบบใหม่

---

# 3. Users and Roles

## 3.1 Caller

ผู้ติดต่อเข้ามาทาง microphone หรือส่ง audio file

ความสามารถ:
- สนทนากับ AI
- ให้ข้อมูล
- รับคำตอบจาก AI
- หยุด/เริ่ม session ตาม interface ที่กำหนด

## 3.2 Call Center Agent / Operator

ผู้ปฏิบัติงานที่ตรวจสอบ session

ความสามารถอย่างน้อย:
- ดูรายการ session
- ดู live transcript
- ดูข้อมูลที่ AI กรอกลง form
- แก้ไขข้อมูลก่อนปิดเคส
- ตรวจสอบ confidence / source citation ที่เกี่ยวข้อง
- export/report ตามสิทธิ์

## 3.3 Supervisor

ความสามารถของ Agent และเพิ่มเติม:
- ดู Dashboard
- ดู Report
- ตรวจสอบคุณภาพการสนทนา
- ตรวจสอบ session history
- ตรวจสอบ AI extraction และ correction

## 3.4 Administrator

ความสามารถทั้งหมดและเพิ่มเติม:
- จัดการ users/roles
- จัดการ AI Role / System Message
- จัดการ model configuration
- จัดการ RAG Knowledge Base
- จัดการ Form Schema / CMS
- จัดการ retention/configuration
- ดู system/AI health

---

# 4. Functional Requirements

## FR-001 Input: Live Microphone

ระบบ SHALL รับเสียงจาก microphone ของเครื่อง Computer ผ่าน Browser โดยค่าเริ่มต้นรองรับ Google Chrome

Acceptance:
- ผู้ใช้อนุญาต microphone access
- ระบบเริ่มรับเสียงได้
- ระบบสามารถหยุด/เริ่มการสนทนา
- ระบบแสดงสถานะ microphone/session

## FR-002 Input: Audio File Upload

ระบบ SHALL รองรับการ Upload file เสียงเพื่อสร้าง session และประมวลผลแบบหลังบ้าน/near-real-time ตามความสามารถของระบบ

Acceptance:
- upload สำเร็จแล้วสร้าง session
- validate file type/size
- แสดง progress/status
- สามารถประมวลผล transcript
- สามารถ map transcript เข้า form

## FR-003 Supported Languages

ระบบ SHALL รองรับ:
- Thai (`th`)
- English (`en`)
- Chinese (`zh`)

ระบบควรตรวจจับภาษาอัตโนมัติ และผู้ดูแลสามารถกำหนด preferred language ต่อ Role/Session ได้

## FR-004 Live Conversation

ระบบ SHALL สนทนาแบบหลายรอบ (multi-turn conversation)

ความต้องการ:
- รักษา conversation context ภายใน session
- AI ต้องสุภาพ
- AI ต้องถามต่อเมื่อข้อมูลสำคัญยังไม่ครบ
- AI ต้องหลีกเลี่ยงการถามซ้ำโดยไม่จำเป็น
- AI ต้องสรุป/ยืนยันข้อมูลสำคัญก่อนปิด session

## FR-005 Goal-oriented Information Extraction

AI SHALL มีเป้าหมายเพื่อเก็บข้อมูลลง Dynamic Form ให้ได้มากที่สุด โดยต้องแยกอย่างน้อย:

- ข้อมูลที่ผู้โทรกล่าวจริง
- ข้อมูลที่ AI สรุปจากคำกล่าว
- ข้อมูลจาก RAG
- ข้อมูลที่ยังไม่ทราบ
- ข้อมูลที่ขัดแย้งกัน
- ข้อมูลที่ผู้โทรปฏิเสธไม่ให้

ห้ามเติมข้อมูลที่ผู้โทรไม่ได้ให้โดยการคาดเดา

## FR-006 Dynamic AI Role

ระบบ SHALL รองรับ AI Role ที่กำหนดด้วย configuration ประกอบด้วยอย่างน้อย:

- Role name
- Role description
- System Message
- Allowed languages
- Conversation objective
- Form Schema ที่ผูกกับ Role
- RAG Knowledge Collections
- LLM model
- STT model
- TTS model
- Safety policy
- Greeting / Closing policy

ผู้ดูแลสามารถสร้าง, แก้ไข, clone, activate/deactivate role ได้

## FR-007 System Message Management

System Message SHALL เป็น configuration ที่แยกจาก source code

ความต้องการ:
- versioning
- draft/published
- effective version ต่อ session
- audit log
- rollback ได้

เมื่อ session เริ่มแล้ว session SHALL อ้างอิง Role/Prompt version ที่แน่นอน เพื่อให้ replay/audit ได้

## FR-008 Live Transcript

ระบบ SHALL แสดง transcript ของ:
- Caller
- AI

อย่างน้อยแสดง:
- speaker
- timestamp
- text
- language
- final/interim state (ถ้ามี)

## FR-009 Dynamic Form CMS

ระบบ SHALL มี CMS สำหรับสร้างแบบฟอร์มโดยไม่ต้องแก้ code

แต่ละ Field ควรมี:
- Field ID / key
- Label
- Description / Meaning
- Data type
- Required / Optional
- Validation
- Allowed values / options
- Display order
- Group/section
- Extraction instruction
- Synonyms / semantic hints
- Sensitivity classification
- Enabled/Disabled
- Version

รองรับ field type อย่างน้อย:
- text
- textarea
- integer
- decimal
- date
- datetime
- boolean
- single select
- multi select
- phone
- address
- structured object

## FR-010 Form Auto-Fill

ระบบ SHALL แปลง transcript เป็น field values แบบ structured data และ fill ลง form

ทุกค่า field ควรเก็บ metadata:
- value
- source utterance / transcript segment
- confidence
- extracted_at
- extractor/model version
- status: proposed / confirmed / corrected / rejected

## FR-011 Human Review

ผู้ปฏิบัติงาน SHALL สามารถแก้ไข field value ที่ AI เติมมา

ระบบ SHALL แยก:
- AI extracted value
- Human corrected value

ห้าม overwrite AI original โดยไม่เก็บ audit history

## FR-012 Uncertainty / Missing Information

เมื่อ AI ไม่พบข้อมูล:
- field ต้องยังว่าง หรือแสดง `Unknown/Not provided`
- ห้ามสร้างข้อมูลขึ้นเอง
- AI สามารถถามคำถามติดตามได้ตามลำดับ priority ของ field

## FR-013 Data Confirmation

ก่อนปิด session ระบบควรให้ AI สรุปข้อมูลสำคัญและขอการยืนยันจากผู้ติดต่อ โดยเฉพาะข้อมูลที่มีความเสี่ยงต่อความผิดพลาดสูง

## FR-014 RAG Knowledge Base

ระบบ SHALL รองรับ Knowledge Base สำหรับ AI

Input:
- TXT/Text
- PDF
- Image

Pipeline ต้องรองรับ:
1. upload
2. file validation
3. parsing
4. OCR สำหรับภาพ/เอกสารภาพ
5. normalization
6. chunking
7. embedding
8. indexing
9. retrieval
10. source attribution

## FR-015 RAG Grounded Answer

AI SHALL ใช้ retrieved knowledge ในการตอบเมื่อคำถามอยู่ในขอบเขต Knowledge Base

ข้อกำหนด:
- ไม่ hallucinate
- หากไม่มีหลักฐานเพียงพอ ให้แจ้งว่าไม่พบข้อมูล/ไม่สามารถยืนยันได้
- response ที่อ้างอิง knowledge ควรเก็บ source document และ chunk reference
- สามารถกำหนด retrieval threshold
- สามารถกำหนด top-k

## FR-016 Knowledge Management

Admin SHALL:
- upload document
- view processing status
- activate/deactivate document
- delete document
- version document
- assign document เข้า collection
- re-index
- ตรวจสอบ parsing/OCR result
- ค้นหา document/chunk

## FR-017 Multiple Knowledge Collections

ระบบ SHALL รองรับหลาย Knowledge Collections เช่น:
- General
- Role-specific
- Department-specific
- Campaign-specific

แต่ละ AI Role สามารถเลือก collection ที่อนุญาตให้ใช้ได้

## FR-018 Audio & Voice Output

ระบบ SHALL รองรับ Text-to-Speech สำหรับคำตอบ AI

ต้องกำหนดได้:
- voice
- language
- speaking rate
- volume
- model

ระบบควรรองรับการเปลี่ยน TTS model โดยไม่แก้ business logic

## FR-019 Dashboard

Dashboard อย่างน้อยควรมี:
- จำนวน sessions
- concurrent sessions
- completed / abandoned / failed
- average session duration
- average response latency
- total audio duration
- STT error/quality indicators
- AI completion rate
- form completion rate
- human correction rate
- missing-field rate
- language distribution
- AI role usage
- RAG usage
- unresolved questions
- top topics / intents
- escalation rate

## FR-020 Reporting

ระบบ SHALL มี Report อย่างน้อย:
- Session Report
- Form Completion Report
- AI Quality Report
- RAG Usage Report
- User/Operator Activity Report
- Error/Failure Report

Report ควร filter ตาม:
- date range
- Role
- language
- status
- operator
- field
- collection

ควร export อย่างน้อย CSV และ JSON; PDF/Excel ให้พิจารณาใน Technical Specification

## FR-021 Search & Session History

ระบบ SHALL สามารถค้นหา session จาก:
- session ID
- date/time
- language
- status
- role
- selected form fields
- phone/contact metadata (ตาม permission)

## FR-022 Audit Trail

ระบบ SHALL audit การเปลี่ยนแปลงสำคัญ:
- prompt/system message
- role
- form schema
- field definitions
- knowledge documents
- user permission
- human correction
- model configuration

---

# 5. Complaint Form Requirement — Drug Complaint Form

เอกสารแนบ **“แบบรับเรื่องร้องเรียนยาเสพติด.pdf”** มี 1 หน้า และเป็นแบบรับเรื่องร้องเรียนที่มีตัวเลือกประเภทการแจ้งเรื่อง ได้แก่ **เงินรางวัล / แจ้งโทษกลั่นแกล้ง / แจ้งหน่วยอื่น** และมีข้อมูลหลักตั้งแต่วัน เวลา เบอร์โทรผู้แจ้ง เพศผู้แจ้ง ไปจนถึงรายละเอียดพฤติการณ์ บุคคล สถานที่ แหล่งที่มา การใช้ยา ผลกระทบ และความประสงค์ให้ติดต่อกลับ โดยท้ายแบบฟอร์มมีตัวเลือกเกี่ยวกับการไม่แจ้งตำรวจ/ฝ่ายปกครองในพื้นที่, ขอให้ ป.ป.ส. ดำเนินการเอง และกรณีต้องการบำบัดโดยไม่ต้องการจับกุมดำเนินคดีสำหรับกรณีเสพอย่างเดียว fileciteturn0file0L2-L32

ข้อมูลที่ระบบ MUST สามารถ model ได้อย่างน้อย:

### 5.1 Header / Reporter
- case type: เงินรางวัล / แจ้งโทษกลั่นแกล้ง / แจ้งหน่วยอื่น
- date
- time
- reporter phone
- reporter gender

### 5.2 Incident
- behavior type:
  - ค้า
  - เสพ
  - ผลิต
  - ลำเลียง
  - สมคบ/ช่วยเหลือ
  - ปล่อยปละละเลย
  - แหล่งค้า
  - แหล่งเสพ
  - อื่น ๆ
- drug type

### 5.3 Subject / Person
- full name
- gender
- nickname / alias
- age
- physical description
- occupation
- workplace
- distinctive characteristics

เอกสารระบุรายละเอียดลักษณะเด่น เช่น หนวด เครา รอยสัก แผลเป็น ความพิการ สิว กระ ไฝ เจาะหู ใส่แว่น จัดฟัน รูปหน้า การแต่งกาย กระเป๋า เครื่องประดับ และ LGBTQ fileciteturn0file0L6-L10

### 5.4 Weapon / Vehicle / Contact
- weapon
- weapon storage/carrying location
- vehicle type/brand/model/color/license/condition
- phone
- FB / Line ID
- other assets
- relatives
- living with

### 5.5 Location
- place name / house number / floor / room
- housing project
- village/community
- soi
- road
- subdistrict
- district
- province
- location characteristics
- directions to complaint location

### 5.6 Drug Source / Storage / Use
- source of drugs: person/place
- price
- stash/storage location
- drug use behavior
- duration of use
- amount per day
- psychiatric symptoms

### 5.7 Impact / Callback / Additional Details
- impact / hardship
- callback request
- callback name
- callback number
- preferred callback time
- other details

### 5.8 Special Handling Preferences
- do not notify local police/administrative authorities
- request ป.ป.ส. to act directly
- request treatment
- do not want arrest/prosecution in “เสพอย่างเดียว” case

**Requirement:** ฟิลด์ข้างต้นต้องเป็น Dynamic Form Schema ที่แก้ไขผ่าน CMS ได้ ไม่ควร hard-code ลง UI

---

# 6. AI Conversation Requirements

## 6.1 Conversation Strategy

AI SHALL ใช้ goal-oriented dialogue:

1. Greeting
2. Explain purpose/consent as configured
3. Identify case type
4. Collect minimum critical information
5. Ask missing fields based on priority
6. Clarify ambiguous information
7. Validate important details
8. Summarize
9. Ask for confirmation
10. Close/escalate

## 6.2 Question Prioritization

ระบบควรมี field priority:
- Critical
- High
- Medium
- Low

AI ต้องพยายามเก็บ Critical/High ก่อน หากผู้ติดต่อพร้อมให้ข้อมูล

## 6.3 No Guessing

AI SHALL NOT:
- invent person names
- invent addresses
- infer exact dates not stated
- infer phone number
- infer crime behavior without evidence
- fabricate RAG answers
- convert uncertain statements into confirmed facts

## 6.4 Sensitive / High-risk Content

ระบบต้องมี policy สำหรับ:
- personal data
- potentially identifying data
- criminal allegation data
- mental health-related statements
- weapons/drug-related information

AI ต้องสนทนาอย่างเป็นกลาง ไม่ตัดสิน และไม่สร้างข้อกล่าวหาขึ้นเอง

---

# 7. AI Architecture Requirements

ระบบต้องแยก AI capability ออกจาก application business logic

อย่างน้อยต้องมี provider abstraction สำหรับ:
- STT
- LLM
- Embedding
- Reranker (optional)
- TTS
- OCR

แต่ละ provider ต้องสามารถเปลี่ยน model ได้ผ่าน configuration

## 7.1 Model Size Constraint

ผู้ใช้กำหนดให้ LLM/AI model สำหรับระบบหลักอยู่ในช่วงประมาณ **4B–8B parameters** และสามารถเปลี่ยน model ได้

Requirement:
- model registry/configuration
- local inference support
- model health check
- timeout
- retry
- fallback strategy

การเลือก model จริงให้กำหนดใน Technical Specification หลังทดสอบภาษาไทย/อังกฤษ/จีนและ hardware จริง

## 7.2 AI Resource Scaling

ระบบเริ่มต้นจาก 1 concurrent caller

แต่ architecture SHALL เตรียมรองรับการขยาย:
- 1 → N sessions
- queue-based inference
- GPU resource pooling
- multiple inference workers
- horizontal scaling
- backpressure
- session isolation

---

# 8. Browser / UI Requirements

## 8.1 Main Call Center Screen

หน้าจอหลักแบ่ง 2 ด้าน:

### Left Panel — Form

แสดง Dynamic Form และสถานะของแต่ละ field:
- empty
- extracting
- suggested
- confirmed
- corrected
- rejected

### Right Panel — Conversation

แสดง:
- Caller transcript
- AI transcript
- timestamps
- current turn
- system status
- language
- optional source/citation

## 8.2 Responsive UI

ระบบควรรองรับ desktop-first โดย Google Chrome เป็น browser หลัก และควรจัด layout ให้รองรับความละเอียดจอทั่วไปของ operator

---

# 9. Non-Functional Requirements

## NFR-001 Deployment

ระบบทั้งหมด SHALL run in Docker

ทุก service ต้องสามารถสร้าง environment ผ่าน Docker Compose เป็น baseline

## NFR-002 Technology Constraints

Programming language / framework:
- Python
- Node.js
- Next.js

Database:
- PostgreSQL

สามารถเลือก technology อื่นได้ตามความเหมาะสมใน Technical Specification

## NFR-003 Web Application

ระบบ SHALL ใช้งานผ่าน Web Browser

Primary browser:
- Google Chrome

## NFR-004 Internet Access

Application รันบน local machine แต่ SHALL สามารถถูกเข้าถึงจาก Internet ผ่าน Cloudflare โดยเน้น Cloudflare Free plan

Requirement:
- TLS termination
- public hostname/domain configuration
- reverse tunnel/access layer
- ไม่ expose database port สู่ Internet
- ไม่เปิด inference service port สู่ Internet โดยตรง

**Cloudflare Free compatibility เป็น requirement เชิง deployment แต่ข้อจำกัดด้าน traffic/concurrency/feature ต้องถูกตรวจสอบอีกครั้งใน Technical Specification และ POC**

## NFR-005 Performance

เป้าหมายเบื้องต้น (ต้อง benchmark ใน TS):
- UI interaction: responsive
- transcript latency: near real-time
- AI response latency: acceptable conversational latency
- queue must prevent resource exhaustion

ตัวเลข SLO/SLA จริงให้กำหนดหลัง POC hardware/model benchmark

## NFR-006 Reliability

ระบบต้อง:
- recover จาก transient provider failure
- retry เฉพาะ operation ที่ safe
- preserve session state
- preserve transcript
- preserve AI extraction history

## NFR-007 Observability

ต้องมี:
- structured logging
- error tracking
- metrics
- health checks
- AI latency metrics
- queue depth
- model utilization
- DB health
- storage health

---

# 10. Data Requirements

## 10.1 Core Entities

อย่างน้อย:
- User
- Role
- Permission
- AI Role
- Prompt Version
- Call Session
- Participant
- Audio Asset
- Transcript Segment
- Form Template
- Form Version
- Form Field
- Form Value
- Extraction Event
- Knowledge Collection
- Knowledge Document
- Knowledge Chunk
- Embedding Metadata
- AI Model Configuration
- Human Correction
- Audit Event
- Report Definition

## 10.2 Session Identity

แต่ละ session SHALL มี immutable `session_id`

## 10.3 Provenance

ทุก extracted field ควร trace กลับได้ถึง:
`Form Field → Extracted Value → Transcript Segment → Session`

และสำหรับ RAG:
`AI Response → Retrieval → Chunk → Document`

---

# 11. Security Requirements

## 11.1 Authentication

ระบบภายใน SHALL มี authentication สำหรับ operator/admin

## 11.2 Authorization

อย่างน้อย:
- Admin
- Supervisor
- Agent
- Viewer

## 11.3 Least Privilege

ผู้ใช้ต้องเข้าถึงเฉพาะข้อมูลที่ role ของตนอนุญาต

## 11.4 Secrets

API keys/passwords SHALL ไม่เก็บใน source code

ให้ใช้:
- environment variables
- Docker secrets หรือ secret management mechanism ที่เหมาะสม

## 11.5 Database

PostgreSQL SHALL ไม่เปิด public Internet

## 11.6 Audit

การเข้าถึงและแก้ไขข้อมูลสำคัญต้อง audit ได้

---

# 12. Privacy and Data Retention

เนื่องจากระบบอาจจัดเก็บข้อมูลส่วนบุคคลและข้อมูลอ่อนไหว ระบบต้องมี configuration สำหรับ:
- audio retention
- transcript retention
- form retention
- audit retention
- automatic deletion/archiving

Retention policy จริงต้องกำหนดตามหน่วยงาน/กฎหมาย/นโยบายของผู้ใช้งานก่อน Production

ระบบควรรองรับการปิดการเก็บ raw audio ได้ หาก deployment ไม่จำเป็นต้องเก็บ

---

# 13. RAG Requirements in Detail

## 13.1 Ingestion

รองรับ:
- `.txt`
- `.pdf`
- image formats ตามที่กำหนดใน TS

## 13.2 OCR

เอกสาร PDF ที่เป็น scanned image และภาพ SHALL สามารถผ่าน OCR pipeline

## 13.3 Chunk Metadata

ทุก chunk ควรมี:
- document_id
- collection_id
- page
- section
- source filename
- version
- language

## 13.4 Retrieval

รองรับ:
- semantic retrieval
- metadata filtering
- top-k
- similarity threshold
- optional reranking

## 13.5 Citation / Provenance

AI response ที่เกิดจาก RAG ควรสามารถเปิดดู source ได้

---

# 14. CMS Requirements

CMS ต้องจัดการอย่างน้อย 4 configuration domains:

1. **AI Role CMS**
2. **Prompt/System Message CMS**
3. **Dynamic Form CMS**
4. **Knowledge Base CMS**

ทั้งหมดต้องมี:
- create
- read
- update
- activate/deactivate
- version/history
- permission control

Delete ในข้อมูล production ควรใช้ soft-delete

---

# 15. Configuration-driven Architecture Requirement

ห้ามผูก logic หลักของ application เข้ากับ “แบบรับเรื่องร้องเรียนยาเสพติด” เพียงแบบเดียว

ระบบต้องรองรับการเพิ่ม Form Template ใหม่ เช่น:
- Drug Complaint
- General Complaint
- Customer Service
- Incident Report

โดยไม่ต้องแก้ business logic หลัก

---

# 16. Error Handling Requirements

ระบบต้องจัดการอย่างชัดเจนสำหรับ:
- microphone denied
- invalid audio
- unsupported language
- STT failure
- LLM timeout
- TTS failure
- RAG unavailable
- vector index unavailable
- database unavailable
- insufficient model resource
- browser disconnect
- duplicate upload

ผู้ใช้ต้องได้รับข้อความที่เข้าใจได้ และ backend ต้องเก็บ technical error สำหรับ troubleshooting

---

# 17. Concurrency & Scalability

## Phase 1
รองรับ 1 concurrent caller

## Phase 2
รองรับหลาย caller โดยแยก resource ต่อ session

Architecture ต้องเตรียม:
- message/processing queue
- stateless API layer
- persistent session state
- worker pools
- model server abstraction
- autoscaling/horizontal scaling option

ระบบต้องไม่ออกแบบโดย assume ว่า LLM inference จะรองรับ concurrent request ได้ไม่จำกัด

---

# 18. Suggested Technology Categories (for TS)

> ส่วนนี้เป็น **ข้อเสนอระดับ Requirement/Direction** ไม่ใช่การ freeze technology

ควรพิจารณา:
- Frontend: Next.js
- Backend/API: Python (FastAPI) + Node.js/Next.js ตาม boundary ที่เหมาะสม
- DB: PostgreSQL
- Vector store: PostgreSQL + pgvector หรือ vector database แยก หาก scale จำเป็น
- Queue: Redis / broker ที่เหมาะสม
- Object storage: local volume / S3-compatible storage
- Container: Docker + Docker Compose
- Reverse access: Cloudflare Tunnel
- OCR: pluggable OCR service
- STT/LLM/TTS: local model-serving abstraction

Technology selection SHALL be finalized in Technical Specification after benchmark.

---

# 19. Backup & Recovery Requirements

ระบบต้องมี:
- PostgreSQL backup
- configuration backup
- knowledge document backup
- optional audio backup
- restore procedure

ต้องกำหนด RPO/RTO ใน Technical Specification

---

# 20. Acceptance Criteria

ระบบจะถือว่าผ่าน Requirement baseline เมื่อสามารถ:

### AC-01 Audio Input
รับเสียงจาก microphone และไฟล์เสียงได้

### AC-02 Multilingual
ประมวลผล Thai / English / Chinese ได้

### AC-03 Conversation
AI สนทนา multi-turn และถามข้อมูลเพิ่มเติมได้

### AC-04 Form Filling
AI เติม Dynamic Form จากบทสนทนาได้

### AC-05 No Hallucinated Form Data
ข้อมูลที่ไม่ได้รับจาก caller ต้องไม่ถูกเติมเป็น fact

### AC-06 Transcript
แสดงบทสนทนาของ Caller และ AI แบบข้อความ

### AC-07 CMS
Admin สร้าง/แก้ไข field และ meaning ได้

### AC-08 Drug Complaint Form
สร้าง form ตามแบบเอกสารแนบ และสามารถนำไปใช้เป็น template ได้

### AC-09 RAG
Upload text/PDF/image แล้วนำข้อมูลเข้า knowledge base ได้

### AC-10 Grounded Answer
เมื่อไม่มี evidence เพียงพอ AI ต้องไม่สร้างคำตอบจากการคาดเดา

### AC-11 Role Switching
เปลี่ยน AI Role / System Message / RAG collection ผ่าน configuration ได้

### AC-12 Model Switching
สามารถเปลี่ยน AI model ได้โดยไม่ต้อง rewrite application core

### AC-13 Dashboard
มี metrics หลักของ Call Center

### AC-14 Reporting
สร้าง report และ filter ได้

### AC-15 Multi-user
session แยกจากกัน ไม่ปะปน context/form/transcript

### AC-16 Docker
ระบบทั้งหมด deploy ได้ด้วย Docker

### AC-17 Internet
เข้าถึงจาก Internet ผ่าน Cloudflare configuration ได้ โดยไม่เปิด DB ตรงสู่ Internet

### AC-18 Audit
สามารถตรวจสอบว่า field/value มาจาก transcript ส่วนใด และใครแก้ไขเมื่อใด

---

# 21. Out of Scope for This Requirement Specification

เรื่องต่อไปนี้จะไม่ freeze ใน RS และจะไปกำหนดใน Technical Specification:

- รุ่น AI model ที่แน่นอน
- GPU/CPU/RAM specification
- exact STT/TTS/LLM provider
- vector DB implementation
- exact API specification
- exact database schema
- UI wireframe/pixel design
- deployment topology รายละเอียด
- CI/CD implementation
- Kubernetes
- cloud provider อื่นนอกเหนือจาก Cloudflare/local deployment
- exact latency/SLO values หลัง benchmark

---

# 22. Key Design Principles

1. **Configuration over Code** — Role, Prompt, Form และ Knowledge ต้องเปลี่ยนได้โดยไม่แก้ code
2. **Grounded AI** — AI ต้องไม่สร้างข้อมูลขึ้นเอง
3. **Traceability** — ทุกข้อมูลสำคัญต้องย้อนกลับไปยัง source ได้
4. **Human-in-the-loop** — operator แก้ไข/ยืนยันข้อมูลได้
5. **Model Agnostic** — เปลี่ยน model ได้
6. **Session Isolation** — แต่ละ caller แยก context และ data
7. **Scalable from Day 1** — เริ่ม 1 caller แต่ architecture ไม่ตันที่ 1 caller
8. **Security by Default** — ไม่ expose database/inference port โดยตรง
9. **Privacy by Design** — รองรับ retention และ access control
10. **Deployable on Local Docker** — local-first, Internet-accessible ผ่าน Cloudflare

---

# 23. Open Questions Requiring Approval Before Technical Specification

1. ต้องการเก็บ **raw audio** ทุก session หรือเก็บเฉพาะบางประเภท?
2. ต้องการให้ AI **โทรออก/รับสายโทรศัพท์จริง (PSTN/SIP)** ในอนาคตหรือระยะนี้ถือว่า Browser microphone เป็น “Caller Interface” เท่านั้น?
3. ต้องการให้ caller เป็น anonymous ทั้งหมด หรือมี authentication/OTP?
4. ต้องการให้ Operator สามารถ “take over” การสนทนาแบบ human handoff หรือไม่?
5. ต้องมี recording consent message ก่อนเริ่ม session หรือไม่?
6. ข้อกำหนด retention ของข้อมูลและเสียงต้องการกี่วัน/เดือน/ปี?
7. ต้องการ deployment แบบ **CPU only**, **single GPU**, หรือมี GPU หลายตัว?
8. ต้องการให้ RAG knowledge ของแต่ละ Role แยกกันโดยสมบูรณ์หรือมี Global Knowledge ร่วม?
9. ต้องการอนุมัติ field เพิ่มเติมจาก PDF เพื่อช่วยการจัดการระบบ เช่น case status, priority, source, operator, SLA หรือไม่?
10. ต้องการ export รายงานเป็น Excel/PDF เพิ่มจาก CSV/JSON หรือไม่?

---

# 24. Approval Gate

เอกสารนี้จะเป็น **Requirement Specification baseline** สำหรับจัดทำ Technical Specification ต่อเมื่อได้รับการอนุมัติจากผู้กำหนดระบบ

### Approval Status
- [ ] Draft
- [ ] Under Review
- [ ] Approved
- [ ] Rework Required

**Approved By:** ____________________  
**Date:** ____________________  
**Version:** ____________________

---

## Appendix A — Source Form Mapping

Source: `แบบรับเรื่องร้องเรียนยาเสพติด.pdf` (1 page)

ระบบ Dynamic Form ควรสามารถจัดกลุ่ม field ตามเอกสารต้นฉบับ ได้แก่:
- Header/ประเภทการแจ้ง
- Reporter
- พฤติการณ์
- ยาเสพติด
- ข้อมูลผู้ถูกกล่าวถึง
- อาวุธ
- ยานพาหนะ
- ช่องทางติดต่อ
- ทรัพย์สิน/ญาติ/ผู้อยู่อาศัยร่วม
- ที่อยู่
- ลักษณะสถานที่
- คำอธิบายเส้นทาง
- แหล่งที่มายาเสพติด
- ที่เก็บซุกซ่อน
- พฤติกรรมการใช้ยา
- อาการทางจิตเวช
- ผลกระทบ
- การติดต่อกลับ
- รายละเอียดอื่น
- ความประสงค์/การดำเนินการท้ายแบบฟอร์ม

รายการ field นี้อ้างอิงจากข้อความและภาพของแบบฟอร์มหน้า 1 ในไฟล์แนบ โดยไม่เปลี่ยนสาระของฟอร์มต้นฉบับ fileciteturn0file0L2-L32
