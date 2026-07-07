import express from 'express';
import multer from 'multer';
import {
  processInvoice,
  approveInvoice,
  getUserInvoices,
} from '../controllers/invoiceController.js';
import { protect } from '../middleware/auth.js';

const router = express.Router();
const upload = multer({ storage: multer.memoryStorage() });

// All invoice routes require authentication
router.use(protect);

// POST /api/invoices/process -> Process a raw invoice text or file with AI
router.post('/process', upload.single('file'), processInvoice);

// POST /api/invoices/approve -> Approve or Reject a paused high-value invoice
router.post('/approve', approveInvoice);

// GET /api/invoices -> Get all invoices for the logged-in user
router.get('/', getUserInvoices);

export default router;
