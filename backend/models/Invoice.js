import mongoose from 'mongoose';

const invoiceSchema = new mongoose.Schema(
  {
    userId: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'User',
      required: true,
    },
    rawText: {
      type: String,
      required: true,
    },
    status: {
      type: String,
      enum: ['processing', 'completed', 'awaiting_approval', 'rejected', 'error'],
      default: 'processing',
    },
    runId: {
      type: String,
      unique: true,
      sparse: true,
    },
    extractedData: {
      type: mongoose.Schema.Types.Mixed,
      default: null,
    },
    amount: {
      type: Number,
      default: 0,
    },
    category: {
      type: mongoose.Schema.Types.Mixed,
      default: null,
    },
    anomalyReport: {
      type: mongoose.Schema.Types.Mixed,
      default: null,
    },
    finalReport: {
      type: String,
      default: '',
    },
    retryCount: {
      type: Number,
      default: 0,
    },
    confidence: {
      type: Number,
      default: 0,
    },
  },
  {
    timestamps: true,
  }
);

export default mongoose.model('Invoice', invoiceSchema);
