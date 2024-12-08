CREATE TABLE `department` (
  `department_id` INT UNSIGNED NOT NULL COMMENT 'Код подразделения в infosys',
  `department_name` VARCHAR(128) NULL COMMENT 'Название подразделения',
  PRIMARY KEY (`department_id`),
  UNIQUE INDEX `department_name_UNIQUE` (`department_name` ASC))
ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT = 'Факультет / кафедра преподавателя';

ALTER TABLE `department` 
ADD COLUMN `parent_department_id` INT UNSIGNED NULL COMMENT 'Вышестоящее подразделение',
ADD INDEX `fk_parent_department_id_idx` (`parent_department_id` ASC);
ALTER TABLE `department` 
ADD CONSTRAINT `fk_parent_department_id`
  FOREIGN KEY (`parent_department_id`)
  REFERENCES `department` (`department_id`)
  ON DELETE NO ACTION
  ON UPDATE NO ACTION;



insert into department values (1600, 'Факультет компьютерных наук', NULL);
insert into department values (1601, 'Кафедра информационных систем', 1600);
insert into department values (1602, 'Кафедра программирования и информационных технологий', 1600);
insert into department values (1603, 'Кафедра цифровых технологий', 1600);
insert into department values (1605, 'Кафедра технологий обработки и защиты информации', 1600);
insert into department values (1606, 'Кафедра информационных технологий управления', 1600);

insert into department values (600, 'Факультет прикладной математики, информатики и механики', NULL);
insert into department values (601, 'Кафедра вычислительной математики и прикладных информационных технологий', 600);
insert into department values (602, 'Кафедра системного анализа и управления', 600);
insert into department values (604, 'Кафедра механики и компьютерного моделирования', 600);
insert into department values (605, 'Кафедра математического обеспечения ЭВМ', 600);
insert into department values (606, 'Кафедра математического и прикладного анализа', 600);
insert into department values (607, 'Кафедра математических методов исследования операций', 600);
insert into department values (608, 'Кафедра программного обеспечения и администрирования информационных систем', 600);
insert into department values (609, 'Кафедра ERP-систем и бизнес процессов', 600);

insert into department values (700, 'Факультет романо-германской филологии', NULL);
insert into department values (709, 'Кафедра английского языка естественно-научных факультетов', 700);
insert into department values (734, 'Кафедра перевода и профессиональной коммуникации', 700);


insert into department values (900, 'Филологический факультет', NULL);
insert into department values (902, 'Кафедра общего языкознания и стилистики', 900);


insert into department values (1200, 'Юридический факультет', NULL);
insert into department values (1220, 'Кафедра теории и истории государства и права', 1200);



insert into department values (1400, 'Факультет философии и психологии', NULL);
insert into department values (1401, 'Кафедра общей и социальной психологии', 1400);
insert into department values (1403, 'Кафедра онтологии и теории познания', 1400);
insert into department values (1405, 'Кафедра педагогики и педагогической психологии', 1400);
insert into department values (1413, 'Кафедра истории философии и культуры', 1400);


insert into department values (1100, 'Экономический факультет', NULL);
insert into department values (1102, 'Кафедра экономики труда и основ управления', 1100);
insert into department values (1125, 'Кафедра экономики, маркетинга и коммерции', 1100);


insert into department values (400, 'Исторический факультет', NULL);
insert into department values (406, 'Кафедра политической истории', 400);

insert into department values (800, 'Физический факультет', NULL);
insert into department values (801, 'Кафедра общей физики', 800);
insert into department values (802, 'Кафедра теоретической физики', 800);
insert into department values (808, 'Кафедра радиофизики', 800);
insert into department values (809, 'Кафедра электроники', 800);



insert into department values (1000, 'Химический факультет', NULL);
insert into department values (1001, 'Кафедра общей и неорганической химии', 1000);
insert into department values (1002, 'Кафедра аналитической химии', 1000);

commit;

ALTER TABLE `teacher` 
ADD COLUMN `department_id` INT UNSIGNED NOT NULL DEFAULT 1600 AFTER `teacher_id`;

ALTER TABLE `teacher` 
ADD INDEX `teacher_fk_department_idx` (`department_id`);

ALTER TABLE `teacher` 
ADD CONSTRAINT `teacher_fk_department`
  FOREIGN KEY (`department_id`)
  REFERENCES `department` (`department_id`)
  ON DELETE NO ACTION
  ON UPDATE NO ACTION;
