import express from 'express';
import {
  processInvoice,
  approveInvoice,
  getUserInvoices,
} from '../controllers/invoiceController.js';
import { protect } from '../middleware/auth.js';

const router = express.Router();

// All invoice routes require authentication
router.use(protect);

// POST /api/invoices/process -> Process a raw invoice text with AI
router.post('/process', processInvoice);

// POST /api/invoices/approve -> Approve or Reject a paused high-value invoice
router.post('/approve', approveInvoice);

// GET /api/invoices -> Get all invoices for the logged-in user
router.get('/', getUserInvoices);

export default router;
