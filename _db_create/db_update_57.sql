CREATE TABLE `department_priorities` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `student_id` bigint unsigned NOT NULL,
  `priority` int unsigned NOT NULL,
  `specialty_id` int unsigned NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_student_priority` (`student_id`,`priority`),
  UNIQUE KEY `uq_student_specialty` (`student_id`,`specialty_id`),
  KEY `fk_dp_specialty` (`specialty_id`),
  CONSTRAINT `fk_dp_specialty` FOREIGN KEY (`specialty_id`) REFERENCES `specialty` (`specialty_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_dp_student` FOREIGN KEY (`student_id`) REFERENCES `student` (`student_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci

CREATE TABLE `project_seminars` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) COLLATE utf8mb4_general_ci NOT NULL,
  `semester` smallint DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=31 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci

CREATE TABLE `student_ratings` (
  `student_id` bigint unsigned NOT NULL,
  `average_score` float NOT NULL COMMENT 'Средний балл',
  `category` smallint NOT NULL COMMENT '1 — бюджет, 2 — договор, 3 — вне конкурса',
  PRIMARY KEY (`student_id`),
  CONSTRAINT `fk_student_ratings_student` FOREIGN KEY (`student_id`) REFERENCES `student` (`student_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci

CREATE TABLE `project_seminar_priorities` (
  `id` int NOT NULL AUTO_INCREMENT,
  `student_id` bigint unsigned NOT NULL,
  `seminar_id` int NOT NULL,
  `priority_number` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_student_priority` (`student_id`,`priority_number`),
  KEY `fk_priority_seminar` (`seminar_id`),
  CONSTRAINT `fk_priority_seminar` FOREIGN KEY (`seminar_id`) REFERENCES `project_seminars` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_priority_student` FOREIGN KEY (`student_id`) REFERENCES `student` (`student_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=117 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci

CREATE TABLE `student_distributions` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `student_id` bigint unsigned NOT NULL,
  `distribution_type` varchar(20) NOT NULL,
  `item_id` int unsigned NOT NULL,
  `distributed_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `is_original` tinyint(1) DEFAULT '1',
  `exchange_pair_id` int unsigned DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_student_distribution` (`student_id`,`distribution_type`),
  KEY `idx_distributions_student` (`student_id`),
  KEY `idx_distributions_type_item` (`distribution_type`,`item_id`),
  KEY `fk_distribution_exchange_pair` (`exchange_pair_id`),
  CONSTRAINT `fk_distribution_exchange_pair` FOREIGN KEY (`exchange_pair_id`) REFERENCES `exchange_pairs` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_distributions_student` FOREIGN KEY (`student_id`) REFERENCES `student` (`student_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci

CREATE TABLE `exchange_requests` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `student_id` bigint unsigned NOT NULL,
  `exchange_type` varchar(20) NOT NULL,
  `current_item_id` int unsigned NOT NULL,
  `desired_item_id` int unsigned NOT NULL,
  `status` varchar(20) NOT NULL DEFAULT 'open',
  `is_active` tinyint(1) DEFAULT '1',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `student_comment` text,
  PRIMARY KEY (`id`),
  KEY `idx_requests_student` (`student_id`),
  KEY `idx_requests_active` (`exchange_type`,`is_active`,`status`),
  KEY `idx_requests_matching` (`exchange_type`,`current_item_id`,`desired_item_id`,`is_active`),
  CONSTRAINT `fk_requests_student` FOREIGN KEY (`student_id`) REFERENCES `student` (`student_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci

CREATE TABLE `exchange_pairs` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `request1_id` int unsigned NOT NULL,
  `request2_id` int unsigned NOT NULL,
  `initiated_by` bigint unsigned NOT NULL,
  `student1_confirmed` tinyint(1) DEFAULT '0',
  `student2_confirmed` tinyint(1) DEFAULT '0',
  `student1_confirmed_at` timestamp NULL DEFAULT NULL,
  `student2_confirmed_at` timestamp NULL DEFAULT NULL,
  `admin_confirmed` tinyint(1) DEFAULT '0',
  `admin_id` int unsigned DEFAULT NULL,
  `admin_comment` text,
  `admin_processed_at` timestamp NULL DEFAULT NULL,
  `status` varchar(20) NOT NULL DEFAULT 'pending_students',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_pairs_status` (`status`),
  KEY `idx_pairs_requests` (`request1_id`,`request2_id`),
  KEY `idx_pairs_admin` (`admin_id`),
  KEY `fk_pairs_request2` (`request2_id`),
  KEY `fk_pairs_initiator` (`initiated_by`),
  CONSTRAINT `fk_pairs_admin` FOREIGN KEY (`admin_id`) REFERENCES `admin_user` (`admin_user_id`),
  CONSTRAINT `fk_pairs_initiator` FOREIGN KEY (`initiated_by`) REFERENCES `student` (`student_id`),
  CONSTRAINT `fk_pairs_request1` FOREIGN KEY (`request1_id`) REFERENCES `exchange_requests` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_pairs_request2` FOREIGN KEY (`request2_id`) REFERENCES `exchange_requests` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci

CREATE TABLE `exchange_history` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `exchange_pair_id` int unsigned NOT NULL,
  `student1_id` bigint unsigned NOT NULL,
  `student1_old_item_id` int unsigned NOT NULL,
  `student1_new_item_id` int unsigned NOT NULL,
  `student2_id` bigint unsigned NOT NULL,
  `student2_old_item_id` int unsigned NOT NULL,
  `student2_new_item_id` int unsigned NOT NULL,
  `exchange_type` varchar(20) NOT NULL,
  `approved_by` int unsigned DEFAULT NULL,
  `executed_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_history_pair` (`exchange_pair_id`),
  KEY `idx_history_students` (`student1_id`,`student2_id`),
  KEY `idx_history_admin` (`approved_by`),
  CONSTRAINT `fk_history_admin` FOREIGN KEY (`approved_by`) REFERENCES `admin_user` (`admin_user_id`),
  CONSTRAINT `fk_history_pair` FOREIGN KEY (`exchange_pair_id`) REFERENCES `exchange_pairs` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci