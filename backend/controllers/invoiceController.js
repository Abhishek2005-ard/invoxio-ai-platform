import Invoice from '../models/Invoice.js';

/**
 * Helper to safely parse JSON strings returned by the agent.
 * Handles potential markdown JSON blocks.
 */
const safeParseJSON = (str) => {
  if (!str) return null;
  try {
    let cleanStr = str.trim();
    if (cleanStr.startsWith('```')) {
      cleanStr = cleanStr.replace(/^```json\s*/i, '').replace(/```$/, '').trim();
    }
    return JSON.parse(cleanStr);
  } catch (err) {
    console.error('[Invoice Controller] Error parsing JSON from agent, saving raw string instead:', err);
    return str;
  }
};

/**
 * Helper to guarantee a value is cast to a clean string.
 */
const safeString = (val) => {
  if (val === null || val === undefined) return '';
  if (typeof val === 'string') return val;
  if (Array.isArray(val) || typeof val === 'object') {
    try {
      return JSON.stringify(val, null, 2);
    } catch {
      return String(val);
    }
  }
  return String(val);
};

/**
 * Trigger the invoice processing pipeline by sending the raw text to the Python agent.
 */
const processInvoice = async (req, res) => {
  let requestBody = {};
  let rawText = '';

  if (req.file) {
    const base64Data = req.file.buffer.toString('base64');
    rawText = `[Uploaded File: ${req.file.originalname}]`;
    requestBody = {
      file_data: base64Data,
      mime_type: req.file.mimetype,
      file_name: req.file.originalname,
    };
  } else {
    const { invoiceText } = req.body;
    if (!invoiceText) {
      return res.status(400).json({
        success: false,
        message: 'invoiceText or file upload is required',
      });
    }
    rawText = invoiceText;
    requestBody = { invoice_text: invoiceText };
  }

  // 1. Create a processing record in MongoDB
  const invoice = new Invoice({
    userId: req.user._id,
    rawText,
    status: 'processing',
  });

  await invoice.save();

  try {
    const agentBaseUrl = (process.env.AGENT_SERVICE_URL || 'http://localhost:8000').replace(/\/$/, '');
    const agentUrl = `${agentBaseUrl}/api/pipeline/process`;
    
    // 2. Call the Python Agent via Fetch
    const response = await fetch(agentUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Agent returned status ${response.status}: ${errorText}`);
    }

    const data = await response.json();

    // 3. Update the MongoDB invoice record with the results
    invoice.runId = data.run_id;
    invoice.status = data.status; // 'completed' or 'awaiting_approval'
    invoice.amount = data.amount || 0;
    invoice.confidence = data.confidence || 0;
    invoice.retryCount = data.retry_count || 1;

    if (data.status === 'completed') {
      invoice.finalReport = safeString(data.final_report);
      // On completion, we also have validated_json, category, anomaly_report
      invoice.extractedData = safeParseJSON(data.validated_json || data.extracted_json);
      invoice.category = safeParseJSON(data.category);
      invoice.anomalyReport = safeParseJSON(data.anomaly_report);
    } else if (data.status === 'awaiting_approval') {
      invoice.finalReport = 'Awaiting human review for high-value invoice.';
      invoice.extractedData = safeParseJSON(data.extracted_json);
      invoice.category = safeParseJSON(data.category);
      invoice.anomalyReport = safeParseJSON(data.anomaly_report);
    }

    await invoice.save();

    return res.status(200).json({
      success: true,
      data: invoice,
    });

  } catch (error) {
    console.error('[Invoice Controller] Error processing invoice:', error);
    invoice.status = 'error';
    invoice.finalReport = `Error during processing: ${error.message}`;
    await invoice.save();

    return res.status(500).json({
      success: false,
      message: 'Failed to process invoice with AI agent',
      error: error.message,
    });
  }
};

/**
 * Approve or Reject a paused high-value invoice, resuming the pipeline.
 */
const approveInvoice = async (req, res) => {
  const { invoiceId, decision, reviewer } = req.body;

  if (!invoiceId || !decision) {
    return res.status(400).json({
      success: false,
      message: 'invoiceId and decision (approved/rejected) are required',
    });
  }

  try {
    // 1. Find the invoice and verify ownership
    const invoice = await Invoice.findOne({ _id: invoiceId, userId: req.user._id });

    if (!invoice) {
      return res.status(404).json({
        success: false,
        message: 'Invoice not found',
      });
    }

    if (invoice.status !== 'awaiting_approval') {
      return res.status(400).json({
        success: false,
        message: `Invoice is not awaiting approval (current status: ${invoice.status})`,
      });
    }

    const agentBaseUrl = (process.env.AGENT_SERVICE_URL || 'http://localhost:8000').replace(/\/$/, '');
    const agentUrl = `${agentBaseUrl}/api/pipeline/approve`;

    // 2. Call the Python Agent approval endpoint
    const response = await fetch(agentUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        run_id: invoice.runId,
        decision,
        reviewer: reviewer || req.user.email,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Agent approval failed: ${errorText}`);
    }

    const data = await response.json();

    // 3. Update the invoice status based on human decision
    invoice.status = decision === 'rejected' ? 'rejected' : 'completed';
    invoice.finalReport = safeString(data.final_report);

    // If there is any updated data returned upon completion
    if (data.validated_json) {
      invoice.extractedData = safeParseJSON(data.validated_json);
    }
    if (data.category) {
      invoice.category = safeParseJSON(data.category);
    }
    if (data.anomaly_report) {
      invoice.anomalyReport = safeParseJSON(data.anomaly_report);
    }

    await invoice.save();

    return res.status(200).json({
      success: true,
      data: invoice,
    });

  } catch (error) {
    console.error('[Invoice Controller] Error approving invoice:', error);
    return res.status(500).json({
      success: false,
      message: 'Failed to submit approval to AI agent',
      error: error.message,
    });
  }
};

/**
 * Fetch all invoices belonging to the authenticated user.
 */
const getUserInvoices = async (req, res) => {
  try {
    const invoices = await Invoice.find({ userId: req.user._id }).sort({ createdAt: -1 });
    return res.status(200).json({
      success: true,
      count: invoices.length,
      data: invoices,
    });
  } catch (error) {
    console.error('[Invoice Controller] Error fetching invoices:', error);
    return res.status(500).json({
      success: false,
      message: 'Server error fetching invoices',
    });
  }
};

export {
  processInvoice,
  approveInvoice,
  getUserInvoices,
};
