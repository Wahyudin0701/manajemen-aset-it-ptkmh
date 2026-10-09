-- MySQL dump 10.13  Distrib 8.0.30, for Win64 (x86_64)
--
-- Host: localhost    Database: manajemen_aset_it
-- ------------------------------------------------------
-- Server version	8.0.30

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `assets_asset`
--

DROP TABLE IF EXISTS `assets_asset`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `assets_asset` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `asset_code` varchar(50) NOT NULL,
  `name` varchar(150) NOT NULL,
  `serial_number` varchar(100) DEFAULT NULL,
  `purchase_date` date DEFAULT NULL,
  `notes` longtext,
  `category_id` bigint DEFAULT NULL,
  `no_index` varchar(20) DEFAULT NULL,
  `price` decimal(15,2) NOT NULL,
  `qty` int NOT NULL,
  `sum_qty` int NOT NULL,
  `total_price` decimal(15,2) NOT NULL,
  `uom` varchar(50) DEFAULT NULL,
  `brand` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `asset_code` (`asset_code`),
  KEY `assets_asset_category_id_b30c6baf_fk_assets_category_id` (`category_id`),
  CONSTRAINT `assets_asset_category_id_b30c6baf_fk_assets_category_id` FOREIGN KEY (`category_id`) REFERENCES `assets_category` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=76 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `assets_asset`
--

LOCK TABLES `assets_asset` WRITE;
/*!40000 ALTER TABLE `assets_asset` DISABLE KEYS */;
INSERT INTO `assets_asset` VALUES (74,'LNV','Laptop Lenovo ThinkPad T14',NULL,NULL,NULL,10,NULL,0.00,1,0,0.00,'Unit','Lenovo'),(75,'TPL','Travel Router',NULL,NULL,NULL,11,NULL,0.00,1,0,0.00,'Unit','TP-Link');
/*!40000 ALTER TABLE `assets_asset` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `assets_assetassignment`
--

DROP TABLE IF EXISTS `assets_assetassignment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `assets_assetassignment` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `assigned_date` date NOT NULL,
  `returned_date` date DEFAULT NULL,
  `document` varchar(100) DEFAULT NULL,
  `status` varchar(20) NOT NULL,
  `notes` longtext,
  `employee_id` bigint DEFAULT NULL,
  `unit_id` bigint NOT NULL,
  `from_employee_id` bigint DEFAULT NULL,
  `type` varchar(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `assets_assetassignment_unit_id_4cd871eb_fk_assets_assetunit_id` (`unit_id`),
  KEY `assets_assetassignme_from_employee_id_348b47b3_fk_assets_em` (`from_employee_id`),
  KEY `assets_assetassignme_employee_id_b89c8743_fk_assets_em` (`employee_id`),
  CONSTRAINT `assets_assetassignme_employee_id_b89c8743_fk_assets_em` FOREIGN KEY (`employee_id`) REFERENCES `assets_employee` (`id`),
  CONSTRAINT `assets_assetassignme_from_employee_id_348b47b3_fk_assets_em` FOREIGN KEY (`from_employee_id`) REFERENCES `assets_employee` (`id`),
  CONSTRAINT `assets_assetassignment_unit_id_4cd871eb_fk_assets_assetunit_id` FOREIGN KEY (`unit_id`) REFERENCES `assets_assetunit` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=40 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `assets_assetassignment`
--

LOCK TABLES `assets_assetassignment` WRITE;
/*!40000 ALTER TABLE `assets_assetassignment` DISABLE KEYS */;
INSERT INTO `assets_assetassignment` VALUES (37,'2026-10-09',NULL,'','aktif','',13,396,NULL,'handover'),(38,'2026-10-09',NULL,'','aktif','',14,396,13,'mutation'),(39,'2026-10-09',NULL,'','aktif','',14,396,14,'return');
/*!40000 ALTER TABLE `assets_assetassignment` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `assets_assetunit`
--

DROP TABLE IF EXISTS `assets_assetunit`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `assets_assetunit` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `unit_code` varchar(60) NOT NULL,
  `status` varchar(20) NOT NULL,
  `asset_id` bigint NOT NULL,
  `assigned_to_id` bigint DEFAULT NULL,
  `area` varchar(50) DEFAULT NULL,
  `location` varchar(255) DEFAULT NULL,
  `id_uuid` char(32) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unit_code` (`unit_code`),
  UNIQUE KEY `assets_assetunit_id_uuid_28ea19f0_uniq` (`id_uuid`),
  KEY `assets_assetunit_asset_id_a1f4823e_fk_assets_asset_id` (`asset_id`),
  KEY `assets_assetunit_assigned_to_id_e6b0f61c_fk_assets_employee_id` (`assigned_to_id`),
  CONSTRAINT `assets_assetunit_asset_id_a1f4823e_fk_assets_asset_id` FOREIGN KEY (`asset_id`) REFERENCES `assets_asset` (`id`),
  CONSTRAINT `assets_assetunit_assigned_to_id_e6b0f61c_fk_assets_employee_id` FOREIGN KEY (`assigned_to_id`) REFERENCES `assets_employee` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=398 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `assets_assetunit`
--

LOCK TABLES `assets_assetunit` WRITE;
/*!40000 ALTER TABLE `assets_assetunit` DISABLE KEYS */;
INSERT INTO `assets_assetunit` VALUES (396,'LNV-001','tersedia',74,NULL,NULL,NULL,'dc3ad273ede348258e6c3e0cb65813b9'),(397,'TPL-001','tersedia',75,NULL,NULL,NULL,'2a255d402cdf493fa61d6cc828ca1d03');
/*!40000 ALTER TABLE `assets_assetunit` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `assets_category`
--

DROP TABLE IF EXISTS `assets_category`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `assets_category` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `assets_category`
--

LOCK TABLES `assets_category` WRITE;
/*!40000 ALTER TABLE `assets_category` DISABLE KEYS */;
INSERT INTO `assets_category` VALUES (10,'Aset Karyawan'),(11,'Aset Networking');
/*!40000 ALTER TABLE `assets_category` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `assets_employee`
--

DROP TABLE IF EXISTS `assets_employee`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `assets_employee` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `nik` varchar(20) NOT NULL,
  `name` varchar(150) NOT NULL,
  `position` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `nik` (`nik`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `assets_employee`
--

LOCK TABLES `assets_employee` WRITE;
/*!40000 ALTER TABLE `assets_employee` DISABLE KEYS */;
INSERT INTO `assets_employee` VALUES (13,'1011','Budi Santoso','Engineer'),(14,'1012','Rayyan Adam','Staff IT');
/*!40000 ALTER TABLE `assets_employee` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `assets_unitlog`
--

DROP TABLE IF EXISTS `assets_unitlog`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `assets_unitlog` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `timestamp` datetime(6) NOT NULL,
  `action` varchar(20) NOT NULL,
  `notes` longtext,
  `employee_id` bigint DEFAULT NULL,
  `unit_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `assets_unitlog_employee_id_7b2f0357_fk_assets_employee_id` (`employee_id`),
  KEY `assets_unitlog_unit_id_9df34195_fk_assets_assetunit_id` (`unit_id`),
  CONSTRAINT `assets_unitlog_employee_id_7b2f0357_fk_assets_employee_id` FOREIGN KEY (`employee_id`) REFERENCES `assets_employee` (`id`),
  CONSTRAINT `assets_unitlog_unit_id_9df34195_fk_assets_assetunit_id` FOREIGN KEY (`unit_id`) REFERENCES `assets_assetunit` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=533 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `assets_unitlog`
--

LOCK TABLES `assets_unitlog` WRITE;
/*!40000 ALTER TABLE `assets_unitlog` DISABLE KEYS */;
INSERT INTO `assets_unitlog` VALUES (527,'2026-10-09 00:44:00.446705','created','Ditambahkan ke Sistem',NULL,396),(528,'2026-10-09 00:48:32.885031','created','Ditambahkan ke Sistem',NULL,397),(529,'2026-10-09 00:49:05.220446','assigned','Diserahkan melalui Distribusi Aset. ',13,396),(530,'2026-10-09 00:49:18.049833','returned','Mutasi: Dikembalikan oleh pemegang sebelumnya.',13,396),(531,'2026-10-09 00:49:18.050822','assigned','Mutasi: Diserahkan ke pemegang baru. ',14,396),(532,'2026-10-09 00:49:32.972454','returned','Dikembalikan oleh karyawan. ',14,396);
/*!40000 ALTER TABLE `assets_unitlog` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group`
--

LOCK TABLES `auth_group` WRITE;
/*!40000 ALTER TABLE `auth_group` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group_permissions`
--

DROP TABLE IF EXISTS `auth_group_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `group_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group_permissions`
--

LOCK TABLES `auth_group_permissions` WRITE;
/*!40000 ALTER TABLE `auth_group_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_permission`
--

DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_permission` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=53 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_permission`
--

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` VALUES (1,'Can add log entry',1,'add_logentry'),(2,'Can change log entry',1,'change_logentry'),(3,'Can delete log entry',1,'delete_logentry'),(4,'Can view log entry',1,'view_logentry'),(5,'Can add permission',2,'add_permission'),(6,'Can change permission',2,'change_permission'),(7,'Can delete permission',2,'delete_permission'),(8,'Can view permission',2,'view_permission'),(9,'Can add group',3,'add_group'),(10,'Can change group',3,'change_group'),(11,'Can delete group',3,'delete_group'),(12,'Can view group',3,'view_group'),(13,'Can add user',4,'add_user'),(14,'Can change user',4,'change_user'),(15,'Can delete user',4,'delete_user'),(16,'Can view user',4,'view_user'),(17,'Can add content type',5,'add_contenttype'),(18,'Can change content type',5,'change_contenttype'),(19,'Can delete content type',5,'delete_contenttype'),(20,'Can view content type',5,'view_contenttype'),(21,'Can add session',6,'add_session'),(22,'Can change session',6,'change_session'),(23,'Can delete session',6,'delete_session'),(24,'Can view session',6,'view_session'),(25,'Can add category',7,'add_category'),(26,'Can change category',7,'change_category'),(27,'Can delete category',7,'delete_category'),(28,'Can view category',7,'view_category'),(29,'Can add employee',8,'add_employee'),(30,'Can change employee',8,'change_employee'),(31,'Can delete employee',8,'delete_employee'),(32,'Can view employee',8,'view_employee'),(33,'Can add asset',9,'add_asset'),(34,'Can change asset',9,'change_asset'),(35,'Can delete asset',9,'delete_asset'),(36,'Can view asset',9,'view_asset'),(37,'Can add asset assignment',10,'add_assetassignment'),(38,'Can change asset assignment',10,'change_assetassignment'),(39,'Can delete asset assignment',10,'delete_assetassignment'),(40,'Can view asset assignment',10,'view_assetassignment'),(41,'Can add asset unit',11,'add_assetunit'),(42,'Can change asset unit',11,'change_assetunit'),(43,'Can delete asset unit',11,'delete_assetunit'),(44,'Can view asset unit',11,'view_assetunit'),(45,'Can add unit log',12,'add_unitlog'),(46,'Can change unit log',12,'change_unitlog'),(47,'Can delete unit log',12,'delete_unitlog'),(48,'Can view unit log',12,'view_unitlog'),(49,'Can add master asset code',13,'add_masterassetcode'),(50,'Can change master asset code',13,'change_masterassetcode'),(51,'Can delete master asset code',13,'delete_masterassetcode'),(52,'Can view master asset code',13,'view_masterassetcode');
/*!40000 ALTER TABLE `auth_permission` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user`
--

DROP TABLE IF EXISTS `auth_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user` (
  `id` int NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(150) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `email` varchar(254) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user`
--

LOCK TABLES `auth_user` WRITE;
/*!40000 ALTER TABLE `auth_user` DISABLE KEYS */;
INSERT INTO `auth_user` VALUES (1,'pbkdf2_sha256$1000000$SOAlHZsXJOGQG46rKKmzhj$ODm1mzDLlmstmPtG8wtyRizvGWutGrzJgPtHYfhXJZs=','2026-10-08 22:45:38.408714',1,'Admin','Admin IT','PT. KMH','adminit@ptkmh.com',1,1,'2026-10-06 04:45:26.610364');
/*!40000 ALTER TABLE `auth_user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_groups`
--

DROP TABLE IF EXISTS `auth_user_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user_groups` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `group_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_groups_user_id_group_id_94350c0c_uniq` (`user_id`,`group_id`),
  KEY `auth_user_groups_group_id_97559544_fk_auth_group_id` (`group_id`),
  CONSTRAINT `auth_user_groups_group_id_97559544_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `auth_user_groups_user_id_6a12ed8b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user_groups`
--

LOCK TABLES `auth_user_groups` WRITE;
/*!40000 ALTER TABLE `auth_user_groups` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_user_permissions`
--

DROP TABLE IF EXISTS `auth_user_user_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user_user_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_user_permissions_user_id_permission_id_14a6b632_uniq` (`user_id`,`permission_id`),
  KEY `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user_user_permissions`
--

LOCK TABLES `auth_user_user_permissions` WRITE;
/*!40000 ALTER TABLE `auth_user_user_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_user_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_admin_log`
--

DROP TABLE IF EXISTS `django_admin_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_admin_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  `content_type_id` int DEFAULT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_auth_user_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `django_admin_log_chk_1` CHECK ((`action_flag` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_admin_log`
--

LOCK TABLES `django_admin_log` WRITE;
/*!40000 ALTER TABLE `django_admin_log` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_admin_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_content_type`
--

DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_content_type` (
  `id` int NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_content_type`
--

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` VALUES (1,'admin','logentry'),(9,'assets','asset'),(10,'assets','assetassignment'),(11,'assets','assetunit'),(7,'assets','category'),(8,'assets','employee'),(13,'assets','masterassetcode'),(12,'assets','unitlog'),(3,'auth','group'),(2,'auth','permission'),(4,'auth','user'),(5,'contenttypes','contenttype'),(6,'sessions','session');
/*!40000 ALTER TABLE `django_content_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_migrations`
--

DROP TABLE IF EXISTS `django_migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_migrations` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=33 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_migrations`
--

LOCK TABLES `django_migrations` WRITE;
/*!40000 ALTER TABLE `django_migrations` DISABLE KEYS */;
INSERT INTO `django_migrations` VALUES (1,'contenttypes','0001_initial','2026-10-06 04:45:19.838348'),(2,'auth','0001_initial','2026-10-06 04:45:20.307424'),(3,'admin','0001_initial','2026-10-06 04:45:20.443577'),(4,'admin','0002_logentry_remove_auto_add','2026-10-06 04:45:20.451847'),(5,'admin','0003_logentry_add_action_flag_choices','2026-10-06 04:45:20.460334'),(6,'assets','0001_initial','2026-10-06 04:45:20.705860'),(7,'contenttypes','0002_remove_content_type_name','2026-10-06 04:45:20.800280'),(8,'auth','0002_alter_permission_name_max_length','2026-10-06 04:45:20.850564'),(9,'auth','0003_alter_user_email_max_length','2026-10-06 04:45:20.872402'),(10,'auth','0004_alter_user_username_opts','2026-10-06 04:45:20.882272'),(11,'auth','0005_alter_user_last_login_null','2026-10-06 04:45:20.928380'),(12,'auth','0006_require_contenttypes_0002','2026-10-06 04:45:20.930958'),(13,'auth','0007_alter_validators_add_error_messages','2026-10-06 04:45:20.937583'),(14,'auth','0008_alter_user_username_max_length','2026-10-06 04:45:20.993876'),(15,'auth','0009_alter_user_last_name_max_length','2026-10-06 04:45:21.053806'),(16,'auth','0010_alter_group_name_max_length','2026-10-06 04:45:21.072790'),(17,'auth','0011_update_proxy_permissions','2026-10-06 04:45:21.082712'),(18,'auth','0012_alter_user_first_name_max_length','2026-10-06 04:45:21.144386'),(19,'sessions','0001_initial','2026-10-06 04:45:21.183259'),(20,'assets','0002_asset_no_index_asset_price_asset_qty_asset_sum_qty_and_more','2026-10-07 01:29:28.464123'),(21,'assets','0003_remove_asset_status_remove_assetassignment_asset_and_more','2026-10-07 02:20:09.815192'),(22,'assets','0004_unitlog','2026-10-07 03:27:16.100025'),(23,'assets','0005_asset_brand_alter_asset_name_alter_asset_price_and_more','2026-10-07 04:35:31.008017'),(24,'assets','0006_masterassetcode','2026-10-07 06:51:44.683179'),(25,'assets','0007_delete_masterassetcode','2026-10-07 07:05:49.366084'),(26,'assets','0008_remove_assetunit_label_alter_unitlog_action','2026-10-07 15:03:08.062581'),(27,'assets','0009_assetassignment_from_employee_assetassignment_type_and_more','2026-10-07 17:12:23.666064'),(28,'assets','0010_assetunit_area_assetunit_location','2026-10-08 04:22:18.618658'),(29,'assets','0011_assetunit_id_uuid','2026-10-08 06:39:38.623826'),(30,'assets','0012_alter_assetunit_id_uuid','2026-10-08 06:40:29.759200'),(31,'assets','0013_alter_assetassignment_employee_and_more','2026-10-08 23:38:14.912474'),(32,'assets','0014_employee_position','2026-10-09 00:36:13.590701');
/*!40000 ALTER TABLE `django_migrations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_session`
--

LOCK TABLES `django_session` WRITE;
/*!40000 ALTER TABLE `django_session` DISABLE KEYS */;
INSERT INTO `django_session` VALUES ('x5fwvq6f7t6xpstguxtedbf94zrmjw8r','.eJxVjDsOwjAQBe_iGln-J6ak5wzWeneNA8iR4qRC3B0ipYD2zcx7iQTbWtPWeUkTibPQ4vS7ZcAHtx3QHdptlji3dZmy3BV50C6vM_Hzcrh_BxV6_dbsgVzwozUqRJtHtGhJh2hwUMX4QhCLjYQcFJB2mjgUGBRwMcrl6MT7A-GCOC4:1xEwrq:2G1tQRKInY4FvkuoROsL7kG4nq48IG_aAAgHBxYwFug','2026-10-22 22:45:38.413135');
/*!40000 ALTER TABLE `django_session` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-10-09 10:37:45
