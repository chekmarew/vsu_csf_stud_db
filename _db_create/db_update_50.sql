ALTER TABLE `certificate_of_study` 
ADD COLUMN `certificate_of_study_comment` VARCHAR(4000) CHARACTER SET 'utf8mb4' COLLATE 'utf8mb4_general_ci' NULL COMMENT 'Комментарий к справке' AFTER `certificate_of_study_with_official_seal`;

set sql_safe_updates=0;
update certificate_of_study set certificate_of_study_comment='Требуется гербовая печать' where certificate_of_study_with_official_seal=1 and certificate_of_study_with_holidays_period=0;
update certificate_of_study set certificate_of_study_comment='Указать в справке каникулярный период' where certificate_of_study_with_official_seal=0 and certificate_of_study_with_holidays_period=1;
update certificate_of_study set certificate_of_study_comment='Требуется гербовая печать, Указать в справке каникулярный период' where certificate_of_study_with_official_seal=1 and certificate_of_study_with_holidays_period=1;
commit;


ALTER TABLE `certificate_of_study` 
DROP COLUMN `certificate_of_study_with_official_seal`,
DROP COLUMN `certificate_of_study_with_holidays_period`;