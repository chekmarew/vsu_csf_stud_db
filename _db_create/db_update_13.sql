-- insert into subject values(0, 'История 0');
-- SET SQL_SAFE_UPDATES = 0;
-- update curriculum_unit set subject_id=0 where subject_id=1;
-- update curriculum_unit set subject_id=1 where subject_id=2;

-- update curriculum_unit set subject_id=2 where subject_id=0;
-- delete from subject where subject_id=0;
-- update subject set subject_name=   'История_' where subject_id=1;
-- update subject set subject_name=   'Иностранный язык' where subject_id=2;
-- update subject set subject_name=   'История' where subject_id=1;

-- commit;


ALTER TABLE `student` 
ADD COLUMN `student_foreigner` TINYINT(1) NOT NULL DEFAULT 0 'Флаг - иностранный студент';
