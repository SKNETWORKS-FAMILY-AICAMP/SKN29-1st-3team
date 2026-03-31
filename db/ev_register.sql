USE ev_dashboard;

-- 1. 코드 테이블 생성 (타입을 INT로 최적화)
CREATE TABLE IF NOT EXISTS code_vhcty_asort (
    code INT PRIMARY KEY COMMENT '차종코드',
    name VARCHAR(10) NOT NULL COMMENT '차종명'
) COMMENT='차종코드';

CREATE TABLE IF NOT EXISTS code_sexdstn (
    code INT PRIMARY KEY COMMENT '성별구분코드',
    name VARCHAR(10) NOT NULL COMMENT '성별명'
) COMMENT='성별구분코드';

CREATE TABLE IF NOT EXISTS code_agrde (
    code INT PRIMARY KEY COMMENT '연령대코드',
    name VARCHAR(10) NOT NULL COMMENT '연령대명'
) COMMENT='연령대코드';

-- 2. 코드 초기 데이터 입력
INSERT IGNORE INTO code_vhcty_asort (code, name) VALUES (1,'승용'), (2,'승합'), (3,'화물'), (4,'특수');
INSERT IGNORE INTO code_sexdstn (code, name) VALUES (1,'남자'), (2,'여자'), (0,'법인');
INSERT IGNORE INTO code_agrde (code, name) VALUES (0,'법인'), (1,'10대'), (2,'20대'), (3,'30대'), (4,'40대'), (5,'50대'), (6,'60대'), (7,'70대'), (8,'80대');

-- 3. 통계 테이블 생성
CREATE TABLE IF NOT EXISTS car_registration_stats (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    regist_yy        INT NOT NULL COMMENT '등록년',
    regist_mt        INT NOT NULL COMMENT '등록월',
    vhcty_asort_code INT COMMENT '차종코드',
    sexdstn          INT COMMENT '성별코드',
    agrde            INT COMMENT '연령대코드',
    cnt              INT DEFAULT 0 COMMENT '등록대수',
    INDEX idx_ym     (regist_yy, regist_mt),
    INDEX idx_vhcty  (vhcty_asort_code)
) COMMENT='자동차_신규등록_통계';

ALTER TABLE car_registration_stats
ADD CONSTRAINT fk_vhcty
FOREIGN KEY (vhcty_asort_code) REFERENCES code_vhcty_asort(code);

ALTER TABLE car_registration_stats
ADD CONSTRAINT fk_sex
FOREIGN KEY (sexdstn) REFERENCES code_sexdstn(code);

ALTER TABLE car_registration_stats
ADD CONSTRAINT fk_agrde
FOREIGN KEY (agrde) REFERENCES code_agrde(code);

-- 월별 정책 뉴스 수 테이블 생성
CREATE TABLE IF NOT EXISTS ev_news_monthly (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    year       INT NOT NULL COMMENT '연도',
    month      INT NOT NULL COMMENT '월',
    news_count INT NOT NULL COMMENT '뉴스 기사 수',
    UNIQUE KEY uq_year_month (year, month)
) COMMENT='월별_전기차_정책_뉴스_수';