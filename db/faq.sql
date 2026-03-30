CREATE TABLE faq (
    id       INT AUTO_INCREMENT PRIMARY KEY,
    question TEXT         NOT NULL COMMENT 'FAQ 질문 내용',
    answer   LONGTEXT     NOT NULL COMMENT 'FAQ 답변 내용',
    category VARCHAR(100) COMMENT 'FAQ 카테고리',
    source   VARCHAR(100) NOT NULL COMMENT '정보 출처'
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;