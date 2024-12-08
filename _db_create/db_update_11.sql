ALTER TABLE `curriculum_unit` 
DROP INDEX `UNIQUE` ,
ADD UNIQUE INDEX `UNIQUE` (`stud_group_id`, `subject_id`);

SET SQL_SAFE_UPDATES = 0;
update admin_user set admin_user_email = null where admin_user_email='';
update student set student_email = null where student_email='';
update teacher set teacher_email = null where teacher_email='';
commit;


ALTER TABLE `admin_user` 
ADD UNIQUE INDEX `admin_user_email_UNIQUE` (`admin_user_email`),
ADD UNIQUE INDEX `admin_user_phone_UNIQUE` (`admin_user_phone`);



ALTER TABLE `student` 
ADD UNIQUE INDEX `student_email_UNIQUE` (`student_email`),
ADD UNIQUE INDEX `student_phone_UNIQUE` (`student_phone`);



ALTER TABLE `teacher` 
ADD UNIQUE INDEX `teacher_email_UNIQUE` (`teacher_email`),
ADD UNIQUE INDEX `teacher_phone_UNIQUE` (`teacher_phone`);
