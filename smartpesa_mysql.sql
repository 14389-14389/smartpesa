-- phpMyAdmin SQL Dump
-- SmartPesa Database Schema for MySQL/MariaDB
-- Generated for XAMPP

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `smartpesa_db`
--
DROP DATABASE IF EXISTS `smartpesa_db`;
CREATE DATABASE IF NOT EXISTS `smartpesa_db` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `smartpesa_db`;

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `email` varchar(255) NOT NULL,
  `full_name` varchar(255) DEFAULT NULL,
  `hashed_password` varchar(255) NOT NULL,
  `is_active` tinyint(1) DEFAULT 1,
  `is_admin` tinyint(1) DEFAULT 0,
  `role` varchar(50) DEFAULT 'user',
  `created_at` datetime DEFAULT current_timestamp(),
  `last_login` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`email`, `full_name`, `hashed_password`, `is_active`, `is_admin`, `role`, `created_at`) VALUES
('test@example.com', 'Test User', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj2N6hHq9kfq', 1, 1, 'admin', NOW()),
('john@example.com', 'John Doe', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj2N6hHq9kfq', 1, 0, 'user', NOW()),
('jane@example.com', 'Jane Smith', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj2N6hHq9kfq', 1, 0, 'user', NOW());

-- --------------------------------------------------------

--
-- Table structure for table `businesses`
--

CREATE TABLE `businesses` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `owner_id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `type` varchar(100) DEFAULT NULL,
  `currency` varchar(10) DEFAULT 'KES',
  `is_active` tinyint(1) DEFAULT 1,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT NULL ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `owner_id` (`owner_id`),
  CONSTRAINT `businesses_ibfk_1` FOREIGN KEY (`owner_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `businesses`
--

INSERT INTO `businesses` (`owner_id`, `name`, `type`, `currency`, `created_at`) VALUES
(1, 'Tech Solutions Ltd', 'retail', 'KES', NOW()),
(1, 'Digital Innovations', 'service', 'KES', NOW()),
(2, 'John\'s Grocery', 'retail', 'KES', NOW()),
(3, 'Jane\'s Consulting', 'service', 'KES', NOW());

-- --------------------------------------------------------

--
-- Table structure for table `transactions`
--

CREATE TABLE `transactions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `business_id` int(11) NOT NULL,
  `amount` decimal(15,2) NOT NULL,
  `type` varchar(50) NOT NULL,
  `category` varchar(100) NOT NULL,
  `description` text DEFAULT NULL,
  `reference` varchar(255) DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT NULL ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `business_id` (`business_id`),
  CONSTRAINT `transactions_ibfk_1` FOREIGN KEY (`business_id`) REFERENCES `businesses` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `transactions`
--

INSERT INTO `transactions` (`business_id`, `amount`, `type`, `category`, `description`, `created_at`) VALUES
(1, 250000.00, 'income', 'Sales', 'Product sales - January', NOW()),
(1, 45000.00, 'expense', 'Rent', 'Office rent - January', NOW()),
(1, 15000.00, 'expense', 'Utilities', 'Electricity bill', NOW()),
(1, 120000.00, 'income', 'Sales', 'Consulting services', NOW()),
(2, 180000.00, 'income', 'Services', 'Web development project', NOW()),
(3, 85000.00, 'income', 'Sales', 'Grocery sales', NOW());

-- --------------------------------------------------------

--
-- Table structure for table `inventory`
--

CREATE TABLE `inventory` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `business_id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `sku` varchar(100) DEFAULT NULL,
  `quantity` decimal(15,2) DEFAULT 0.00,
  `unit` varchar(50) DEFAULT 'pieces',
  `price_per_unit` decimal(15,2) DEFAULT 0.00,
  `reorder_level` decimal(15,2) DEFAULT 10.00,
  `category` varchar(100) DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT 1,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT NULL ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `sku` (`sku`),
  KEY `business_id` (`business_id`),
  CONSTRAINT `inventory_ibfk_1` FOREIGN KEY (`business_id`) REFERENCES `businesses` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `inventory`
--

INSERT INTO `inventory` (`business_id`, `name`, `sku`, `quantity`, `unit`, `price_per_unit`, `reorder_level`, `category`) VALUES
(1, 'Laptop', 'TECH-001', 15.00, 'pieces', 75000.00, 5.00, 'Electronics'),
(1, 'Printer', 'TECH-002', 3.00, 'pieces', 20000.00, 5.00, 'Electronics'),
(1, 'Office Chair', 'FURN-001', 8.00, 'pieces', 8500.00, 3.00, 'Furniture'),
(3, 'Milk', 'GR-001', 50.00, 'liters', 120.00, 20.00, 'Dairy'),
(3, 'Bread', 'GR-002', 30.00, 'pieces', 60.00, 10.00, 'Bakery');

-- --------------------------------------------------------

--
-- Table structure for table `suppliers`
--

CREATE TABLE `suppliers` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `business_id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `contact_person` varchar(255) DEFAULT NULL,
  `phone` varchar(50) DEFAULT NULL,
  `email` varchar(255) DEFAULT NULL,
  `address` text DEFAULT NULL,
  `payment_terms` varchar(100) DEFAULT 'Net 30',
  `is_active` tinyint(1) DEFAULT 1,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT NULL ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `business_id` (`business_id`),
  CONSTRAINT `suppliers_ibfk_1` FOREIGN KEY (`business_id`) REFERENCES `businesses` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `suppliers`
--

INSERT INTO `suppliers` (`business_id`, `name`, `contact_person`, `phone`, `email`, `payment_terms`) VALUES
(1, 'Tech Supplies Ltd', 'Michael Okoth', '+254712345678', 'michael@techsupplies.co.ke', 'Net 30'),
(1, 'Office Furnishings', 'Sarah Wanjiku', '+254723456789', 'sarah@officefurnishings.co.ke', 'Net 45'),
(3, 'Fresh Farms Ltd', 'James Kariuki', '+254734567890', 'james@freshfarms.co.ke', 'Net 15');

-- --------------------------------------------------------

--
-- Table structure for table `payments`
--

CREATE TABLE `payments` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `supplier_id` int(11) NOT NULL,
  `amount` decimal(15,2) NOT NULL,
  `payment_date` date NOT NULL,
  `due_date` date DEFAULT NULL,
  `method` varchar(50) DEFAULT 'bank_transfer',
  `reference` varchar(255) DEFAULT NULL,
  `notes` text DEFAULT NULL,
  `paid` tinyint(1) DEFAULT 0,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT NULL ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `supplier_id` (`supplier_id`),
  CONSTRAINT `payments_ibfk_1` FOREIGN KEY (`supplier_id`) REFERENCES `suppliers` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `payments`
--

INSERT INTO `payments` (`supplier_id`, `amount`, `payment_date`, `due_date`, `method`, `reference`, `paid`) VALUES
(1, 150000.00, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 10 DAY), 'bank_transfer', 'TRF-2024-001', 1),
(1, 60000.00, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 15 DAY), 'bank_transfer', 'TRF-2024-002', 1),
(2, 68000.00, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 20 DAY), 'cheque', 'CHQ-001', 1),
(3, 6000.00, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 5 DAY), 'cash', NULL, 1);

-- --------------------------------------------------------

--
-- Table structure for table `notifications`
--

CREATE TABLE `notifications` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `business_id` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `title` varchar(255) NOT NULL,
  `message` text NOT NULL,
  `type` varchar(50) DEFAULT 'info',
  `priority` varchar(20) DEFAULT 'normal',
  `is_read` tinyint(1) DEFAULT 0,
  `read_at` datetime DEFAULT NULL,
  `action_url` varchar(500) DEFAULT NULL,
  `expires_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT NULL ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `business_id` (`business_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `notifications_ibfk_1` FOREIGN KEY (`business_id`) REFERENCES `businesses` (`id`) ON DELETE CASCADE,
  CONSTRAINT `notifications_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `notifications`
--

INSERT INTO `notifications` (`business_id`, `user_id`, `title`, `message`, `type`, `priority`) VALUES
(1, 1, 'Low Stock Alert', 'Printer is running low on stock (3 units remaining)', 'warning', 'high'),
(1, 1, 'Payment Due', 'Payment to Tech Supplies Ltd is due in 5 days', 'info', 'normal'),
(3, 2, 'Low Stock Alert', 'Milk is below reorder level (50 liters)', 'warning', 'high');

-- --------------------------------------------------------

--
-- Table structure for table `credit_scores`
--

CREATE TABLE `credit_scores` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `business_id` int(11) NOT NULL,
  `smartpesa_score` int(11) DEFAULT 0,
  `revenue_consistency_score` decimal(5,2) DEFAULT 0.00,
  `cash_buffer_ratio` decimal(5,2) DEFAULT 0.00,
  `debt_coverage_capacity` decimal(5,2) DEFAULT 0.00,
  `inventory_health_score` decimal(5,2) DEFAULT 0.00,
  `factors` json DEFAULT NULL,
  `calculated_at` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `business_id` (`business_id`),
  CONSTRAINT `credit_scores_ibfk_1` FOREIGN KEY (`business_id`) REFERENCES `businesses` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `credit_scores`
--

INSERT INTO `credit_scores` (`business_id`, `smartpesa_score`, `revenue_consistency_score`, `cash_buffer_ratio`, `debt_coverage_capacity`, `inventory_health_score`, `factors`) VALUES
(1, 684, 75.00, 60.00, 80.00, 70.00, '{"payment_history": "good", "business_age": 2, "transaction_volume": "high"}'),
(2, 592, 60.00, 45.00, 70.00, 65.00, '{"payment_history": "average", "business_age": 1, "transaction_volume": "medium"}'),
(3, 723, 85.00, 75.00, 85.00, 80.00, '{"payment_history": "excellent", "business_age": 3, "transaction_volume": "high"}');

COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
