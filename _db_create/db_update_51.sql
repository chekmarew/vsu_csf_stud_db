ALTER TABLE `certificate_of_study` 
ADD COLUMN `certificate_of_study_student_status` ENUM('study', 'alumnus', 'expelled', 'academic_leave') NOT NULL DEFAULT 'study' AFTER `certificate_of_study_course`;


ALTER TABLE `specialty` 
CHANGE COLUMN `education_standart` `education_standart` ENUM('', 'fgos3+', 'fgos3++') CHARACTER SET 'latin1' COLLATE 'latin1_general_ci' NOT NULL DEFAULT 'fgos3++' COMMENT 'Образовательный стандарт (ФГОС3+ или ФГОС3++)' ;
