CREATE TABLE faq (
    id       INT AUTO_INCREMENT PRIMARY KEY,
    question TEXT         NOT NULL,
    answer   LONGTEXT     NOT NULL,
    category VARCHAR(100),
    source   VARCHAR(100) NOT NULL
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;