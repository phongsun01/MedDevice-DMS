-- ============================================================
-- MedDevice DMS - SurrealDB Schema Definition
-- Version: 1.0.3
-- ============================================================

-- Vietnamese text analyzer
DEFINE ANALYZER vn_analyzer TOKENIZERS blank, class FILTERS lowercase, ascii;

-- ============================================================
-- TABLE: category
-- ============================================================
DEFINE TABLE category SCHEMAFULL
    PERMISSIONS
        FOR select, create, update, delete WHERE $auth != NONE;

DEFINE FIELD name        ON category TYPE string;
DEFINE FIELD description ON category TYPE option<string>;
DEFINE FIELD created_at  ON category TYPE datetime DEFAULT time::now();

-- ============================================================
-- TABLE: device_group (tránh conflict keyword "group")
-- ============================================================
DEFINE TABLE device_group SCHEMAFULL
    PERMISSIONS
        FOR select, create, update, delete WHERE $auth != NONE;

DEFINE FIELD name        ON device_group TYPE string;
DEFINE FIELD description ON device_group TYPE option<string>;
DEFINE FIELD category    ON device_group TYPE record<category>;
DEFINE FIELD created_at  ON device_group TYPE datetime DEFAULT time::now();

-- ============================================================
-- TABLE: device
-- ============================================================
DEFINE TABLE device SCHEMAFULL
    PERMISSIONS
        FOR select, create, update, delete WHERE $auth != NONE;

DEFINE FIELD name         ON device TYPE string;
DEFINE FIELD model        ON device TYPE string;
DEFINE FIELD brand        ON device TYPE string;
DEFINE FIELD origin       ON device TYPE option<string>;
DEFINE FIELD year         ON device TYPE option<int>;
DEFINE FIELD device_group ON device TYPE record<device_group>;
DEFINE FIELD notes        ON device TYPE option<string>;
DEFINE FIELD created_at   ON device TYPE datetime DEFAULT time::now();
DEFINE FIELD updated_at   ON device TYPE datetime DEFAULT time::now();

-- ============================================================
-- TABLE: document
-- ============================================================
DEFINE TABLE document SCHEMAFULL
    PERMISSIONS
        FOR select, create, update, delete WHERE $auth != NONE;

DEFINE FIELD device       ON document TYPE record<device>;
DEFINE FIELD doc_type     ON document TYPE string;
DEFINE FIELD sub_type     ON document TYPE option<string>;
DEFINE FIELD file_path    ON document TYPE option<string>;
DEFINE FIELD file_url     ON document TYPE option<string>;
DEFINE FIELD content_text ON document TYPE option<string>;
DEFINE FIELD metadata     ON document TYPE object FLEXIBLE;
DEFINE FIELD uploaded_at  ON document TYPE datetime DEFAULT time::now();

-- ============================================================
-- TABLE: audit_log (bắt buộc cho phần mềm y tế)
-- ============================================================
DEFINE TABLE audit_log SCHEMAFULL
    PERMISSIONS
        FOR select WHERE $auth != NONE
        FOR create WHERE $auth != NONE;

DEFINE FIELD action           ON audit_log TYPE string;
DEFINE FIELD table_name       ON audit_log TYPE string;
DEFINE FIELD record_id        ON audit_log TYPE string;
DEFINE FIELD telegram_user_id ON audit_log TYPE option<string>;
DEFINE FIELD timestamp        ON audit_log TYPE datetime DEFAULT time::now();
DEFINE FIELD changes          ON audit_log TYPE object FLEXIBLE;

-- ============================================================
-- INDEXES
-- ============================================================

-- Content indexes
DEFINE INDEX idx_content  ON document FIELDS content_text;
DEFINE INDEX idx_metadata ON document FIELDS metadata;

-- Device lookup indexes
DEFINE INDEX idx_device_name  ON device FIELDS name;
DEFINE INDEX idx_device_model ON device FIELDS model;
DEFINE INDEX idx_device_brand ON device FIELDS brand;

-- Document lookup indexes
DEFINE INDEX idx_doc_type   ON document FIELDS doc_type;
DEFINE INDEX idx_doc_device ON document FIELDS device;

-- Audit log indexes
DEFINE INDEX idx_audit_table     ON audit_log FIELDS table_name;
DEFINE INDEX idx_audit_timestamp ON audit_log FIELDS timestamp;
