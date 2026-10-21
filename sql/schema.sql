-- MySQL 8.0+. Run against an empty project database, never a production schema.

CREATE TABLE IF NOT EXISTS `stores` (
  `store_nbr` INT NOT NULL PRIMARY KEY,
  `city` VARCHAR(100),
  `state` VARCHAR(100),
  `type` VARCHAR(10),
  `cluster` INT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;

CREATE TABLE IF NOT EXISTS `families` (
  `family` VARCHAR(100) NOT NULL PRIMARY KEY
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;

CREATE TABLE IF NOT EXISTS `dates` (
  `date` DATE NOT NULL PRIMARY KEY,
  `year` INT,
  `month` VARCHAR(7),
  `weekday` INT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;

CREATE TABLE IF NOT EXISTS `sales` (
  `id` BIGINT NOT NULL PRIMARY KEY,
  `date` DATE NOT NULL,
  `store_nbr` INT NOT NULL,
  `family` VARCHAR(100) NOT NULL,
  `sales` DOUBLE,
  `onpromotion` DOUBLE,
  FOREIGN KEY (`store_nbr`) REFERENCES stores(`store_nbr`),
  FOREIGN KEY (`family`) REFERENCES families(`family`),
  FOREIGN KEY (`date`) REFERENCES dates(`date`),
  UNIQUE KEY uq_store_family_date (`date`,`store_nbr`,`family`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;

CREATE TABLE IF NOT EXISTS `transactions` (
  `date` DATE NOT NULL,
  `store_nbr` INT NOT NULL,
  `transactions` BIGINT,
  PRIMARY KEY (`date`,`store_nbr`),
  FOREIGN KEY (`store_nbr`) REFERENCES stores(`store_nbr`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;

CREATE TABLE IF NOT EXISTS `holidays` (
  `event_id` INT NOT NULL PRIMARY KEY,
  `date` DATE,
  `type` VARCHAR(32),
  `locale` VARCHAR(32),
  `locale_name` VARCHAR(100),
  `description` VARCHAR(255),
  `transferred` VARCHAR(10)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;