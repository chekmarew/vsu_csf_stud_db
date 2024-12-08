CREATE TABLE `favorite_teacher_student` (
  `teacher_id` INT UNSIGNED NOT NULL,
  `student_id` BIGINT UNSIGNED NOT NULL,
  PRIMARY KEY (`teacher_id`, `student_id`))
  COMMENT='Для формирования раздела \"Мой список студентов\" у преподавателей';
  
ALTER TABLE `favorite_teacher_student` 
ADD CONSTRAINT `fk_teacher_id`
  FOREIGN KEY (`teacher_id`)
  REFERENCES `teacher` (`teacher_id`)
  ON DELETE CASCADE
  ON UPDATE CASCADE,
ADD CONSTRAINT `fk_student_id`
  FOREIGN KEY (`student_id`)
  REFERENCES `student` (`student_id`)
  ON DELETE CASCADE
  ON UPDATE CASCADE;

-- Добавить иностранных студентов в список к Швырёвой А.В.
insert into favorite_teacher_student
(select 21, student_id from student where student_status='study' and mod(student_id, 10000) between 5000 and 5999 );

commit;
