import React, { useRef, useState } from 'react';
import {
  AlertCircle,
  Camera,
  CheckCircle2,
  Clock,
  Cpu,
  Eye,
  FileVideo,
  Layers,
  Play,
  Sparkles,
  Upload,
  Video,
} from 'lucide-react';
import { api } from '../services/api';
import type {
  CCTVAnalysisResponse,
  CCTVFrameResult,
  ReconciliationResult,
  ShelfDetectionResponse,
} from '../types';

interface VisionTabProps {
  onInventoryUpdated: () => void;
}

export const VisionTab: React.FC<VisionTabProps> = ({ onInventoryUpdated }) => {
  const [activeSubTab, setActiveSubTab] = useState<'image' | 'cctv'>('image');

  // Shelf Image State
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [confThreshold, setConfThreshold] = useState<number>(0.25);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [detectionResult, setDetectionResult] = useState<ShelfDetectionResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [fusionResults, setFusionResults] = useState<ReconciliationResult[] | null>(null);
  const [isFusing, setIsFusing] = useState<boolean>(false);

  // CCTV Video State
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [videoPreviewUrl, setVideoPreviewUrl] = useState<string | null>(null);
  const [sampleInterval, setSampleInterval] = useState<number>(3.0);
  const [maxFrames, setMaxFrames] = useState<number>(30);
  const [isVideoLoading, setIsVideoLoading] = useState<boolean>(false);
  const [videoResult, setVideoResult] = useState<CCTVAnalysisResponse | null>(null);
  const [isCctvFusing, setIsCctvFusing] = useState<boolean>(false);
  const [cctvFusionResults, setCctvFusionResults] = useState<ReconciliationResult[] | null>(null);
  const [selectedFrame, setSelectedFrame] = useState<CCTVFrameResult | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const videoInputRef = useRef<HTMLInputElement>(null);

  // Handlers for Shelf Image Scanner
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setDetectionResult(null);
      setFusionResults(null);
      setErrorMsg(null);
    }
  };

  const handleLoadSampleImage = async (filename: string = 'shelf_sample.jpg') => {
    try {
      setErrorMsg(null);
      const file = await api.loadSampleImage(filename);
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setDetectionResult(null);
      setFusionResults(null);
    } catch {
      setErrorMsg(`Failed to load sample shelf image (${filename}).`);
    }
  };

  const handleRunDetection = async () => {
    if (!selectedFile) {
      setErrorMsg('Please select or upload a shelf photo first.');
      return;
    }
    setIsLoading(true);
    setErrorMsg(null);
    setFusionResults(null);

    try {
      const res = await api.detectShelf(selectedFile, confThreshold);
      setDetectionResult(res);
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || err.message || 'Vision detection failed.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleFuseIntoInventory = async () => {
    if (!detectionResult || !detectionResult.class_counts) return;
    setIsFusing(true);
    setErrorMsg(null);

    try {
      const results = await api.fuseVisionCounts(detectionResult.class_counts);
      setFusionResults(results);
      onInventoryUpdated();
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || err.message || 'Failed to fuse vision counts into inventory.');
    } finally {
      setIsFusing(false);
    }
  };

  // Handlers for CCTV Video Ingestion
  const handleVideoFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setVideoFile(file);
      setVideoPreviewUrl(URL.createObjectURL(file));
      setVideoResult(null);
      setCctvFusionResults(null);
      setSelectedFrame(null);
      setErrorMsg(null);
    }
  };

  const handleLoadSampleVideo = async () => {
    try {
      setErrorMsg(null);
      const file = await api.loadSampleVideo();
      setVideoFile(file);
      setVideoPreviewUrl(URL.createObjectURL(file));
      setVideoResult(null);
      setCctvFusionResults(null);
      setSelectedFrame(null);
    } catch {
      setErrorMsg('Failed to load sample CCTV video.');
    }
  };

  const handleRunVideoAnalysis = async () => {
    if (!videoFile) {
      setErrorMsg('Please select a video file for CCTV analysis.');
      return;
    }
    setIsVideoLoading(true);
    setErrorMsg(null);
    setCctvFusionResults(null);
    setSelectedFrame(null);

    try {
      const res = await api.analyzeVideo(videoFile, sampleInterval, maxFrames);
      setVideoResult(res);
      if (res.frame_results && res.frame_results.length > 0) {
        setSelectedFrame(res.frame_results[0]);
      }
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || err.message || 'Video analysis failed.');
    } finally {
      setIsVideoLoading(false);
    }
  };

  const handleFuseCctvIntoInventory = async () => {
    if (!videoResult || !videoResult.aggregated_counts) return;
    setIsCctvFusing(true);
    setErrorMsg(null);

    try {
      const results = await api.fuseVisionCounts(videoResult.aggregated_counts);
      setCctvFusionResults(results);
      onInventoryUpdated();
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || err.message || 'Failed to fuse CCTV counts into inventory.');
    } finally {
      setIsCctvFusing(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Tab Header & Sub-tab switcher */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center space-x-2">
            <Camera className="w-5 h-5 text-emerald-400" />
            <span>AI Shelf Vision & CCTV Video Pipeline</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Ultralytics YOLO shelf observation, visible facing counts, and automated physical-vs-digital ledger fusion
          </p>
        </div>

        <div className="flex p-1 rounded-xl bg-slate-900 border border-slate-800">
          <button
            onClick={() => setActiveSubTab('image')}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
              activeSubTab === 'image'
                ? 'bg-emerald-500 text-slate-950 shadow-md'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Camera className="w-3.5 h-3.5" />
            <span>Shelf Image Scanner</span>
          </button>
          <button
            onClick={() => setActiveSubTab('cctv')}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
              activeSubTab === 'cctv'
                ? 'bg-emerald-500 text-slate-950 shadow-md'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Video className="w-3.5 h-3.5" />
            <span>CCTV Video Ingestion</span>
          </button>
        </div>
      </div>

      {errorMsg && (
        <div className="flex items-center space-x-2 p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {activeSubTab === 'image' ? (
        /* SHELF IMAGE SCANNER SUB-TAB */
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Upload & Parameters */}
          <div className="lg:col-span-5 space-y-4">
            <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-4">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                    <Upload className="w-4 h-4 text-emerald-400" />
                    <span>Upload Shelf Photo</span>
                  </h3>
                  <span className="text-[10px] text-slate-400">or pick a sample:</span>
                </div>
                <div className="grid grid-cols-3 gap-1.5">
                  <button
                    type="button"
                    onClick={() => handleLoadSampleImage('shelf_sample.jpg')}
                    className="px-2 py-1.5 rounded-lg text-[10px] font-bold bg-emerald-500/10 hover:bg-emerald-500/25 text-emerald-300 border border-emerald-500/30 transition flex items-center justify-center space-x-1"
                  >
                    <span>🥤 Drinks Shelf</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => handleLoadSampleImage('dairy_shelf_sample.jpg')}
                    className="px-2 py-1.5 rounded-lg text-[10px] font-bold bg-cyan-500/10 hover:bg-cyan-500/25 text-cyan-300 border border-cyan-500/30 transition flex items-center justify-center space-x-1"
                  >
                    <span>🥛 Dairy Cooler</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => handleLoadSampleImage('snack_shelf_sample.jpg')}
                    className="px-2 py-1.5 rounded-lg text-[10px] font-bold bg-amber-500/10 hover:bg-amber-500/25 text-amber-300 border border-amber-500/30 transition flex items-center justify-center space-x-1"
                  >
                    <span>🍿 Snacks Rack</span>
                  </button>
                </div>
              </div>

              {/* Upload Dropzone */}
              <div
                onClick={() => fileInputRef.current?.click()}
                className="border-2 border-dashed border-slate-700 hover:border-emerald-500/50 rounded-2xl p-6 text-center cursor-pointer transition bg-slate-950/40 hover:bg-slate-900/40 group"
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/jpeg,image/png,image/jpg"
                  className="hidden"
                  onChange={handleFileChange}
                />
                <Camera className="w-10 h-10 text-slate-500 group-hover:text-emerald-400 mx-auto mb-2 transition" />
                <p className="text-xs font-semibold text-slate-200">
                  {selectedFile ? selectedFile.name : 'Click or drop shelf photograph'}
                </p>
                <p className="text-[11px] text-slate-500 mt-1">Supports JPG, PNG up to 15MB</p>
              </div>

              {/* Confidence Threshold Slider */}
              <div>
                <div className="flex items-center justify-between text-xs mb-1">
                  <span className="font-semibold text-slate-300">YOLO Confidence Threshold</span>
                  <span className="font-mono text-emerald-400 font-bold">
                    {Math.round(confThreshold * 100)}%
                  </span>
                </div>
                <input
                  type="range"
                  min="0.10"
                  max="0.90"
                  step="0.05"
                  value={confThreshold}
                  onChange={(e) => setConfThreshold(parseFloat(e.target.value))}
                  className="w-full accent-emerald-500 cursor-pointer"
                />
              </div>

              {/* Actions */}
              <div className="pt-2 flex flex-col gap-2">
                <button
                  id="run-vision-btn"
                  onClick={handleRunDetection}
                  disabled={!selectedFile || isLoading}
                  className="w-full py-2.5 rounded-xl text-xs font-bold bg-emerald-500 hover:bg-emerald-400 text-slate-950 transition shadow-lg shadow-emerald-500/20 active:scale-95 disabled:opacity-50 flex items-center justify-center space-x-2"
                >
                  <Sparkles className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
                  <span>{isLoading ? 'Running YOLO Inference...' : 'Execute Shelf Detection'}</span>
                </button>
              </div>
            </div>

            {/* Model Architecture Info */}
            <div className="glass-panel p-4 rounded-2xl border border-slate-800 text-xs space-y-2">
              <div className="flex items-center space-x-2 text-slate-300 font-semibold">
                <Cpu className="w-4 h-4 text-emerald-400" />
                <span>Detection Engine Specification</span>
              </div>
              <p className="text-[11px] text-slate-400">
                Model: <span className="text-slate-200 font-mono">yolov8n.pt</span> (Ultralytics PyTorch)
              </p>
              <p className="text-[11px] text-slate-400">
                Mode: <span className="text-emerald-400 font-semibold">COCO Validation / Custom Retail Ready</span>
              </p>
            </div>
          </div>

          {/* Right Column: Visual Preview & Detection Results */}
          <div className="lg:col-span-7 space-y-4">
            <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                  <Layers className="w-4 h-4 text-emerald-400" />
                  <span>Detection Results & Visual Overlay</span>
                </h3>
                {detectionResult && (
                  <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold">
                    {detectionResult.total_detected} objects detected
                  </span>
                )}
              </div>

              {/* Annotated Image or Raw Preview */}
              <div className="relative rounded-2xl overflow-hidden bg-slate-950 border border-slate-800 flex items-center justify-center min-h-[320px]">
                {detectionResult?.annotated_image_url ? (
                  <img
                    src={detectionResult.annotated_image_url}
                    alt="YOLO Detection Results"
                    className="w-full max-h-[460px] object-contain"
                  />
                ) : previewUrl ? (
                  <img
                    src={previewUrl}
                    alt="Preview"
                    className="w-full max-h-[460px] object-contain opacity-70"
                  />
                ) : (
                  <div className="text-center p-8 text-slate-500">
                    <Camera className="w-12 h-12 mx-auto mb-2 opacity-30" />
                    <p className="text-xs">No shelf image loaded</p>
                  </div>
                )}
              </div>

              {/* Detection Summary & Fusion Button */}
              {detectionResult && (
                <div className="space-y-4 pt-2">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-xl bg-slate-900 border border-slate-800">
                    <div>
                      <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                        Visible Product Counts
                      </h4>
                      <div className="flex flex-wrap gap-2 mt-2">
                        {Object.entries(detectionResult.class_counts).length > 0 ? (
                          Object.entries(detectionResult.class_counts).map(([cls, cnt]) => (
                            <span
                              key={cls}
                              className="px-2.5 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold"
                            >
                              {cls}: <span className="font-bold text-white">{cnt}</span>
                            </span>
                          ))
                        ) : (
                          <span className="text-xs text-slate-400">
                            No recognized items above threshold. Try adjusting confidence slider.
                          </span>
                        )}
                      </div>
                    </div>

                    <button
                      id="fuse-into-inventory-btn"
                      onClick={handleFuseIntoInventory}
                      disabled={isFusing || Object.keys(detectionResult.class_counts).length === 0}
                      className="px-4 py-2 rounded-xl text-xs font-bold bg-emerald-500 hover:bg-emerald-400 text-slate-950 transition shadow-md shadow-emerald-500/20 active:scale-95 disabled:opacity-50 flex items-center space-x-1.5 flex-shrink-0"
                    >
                      <Layers className="w-3.5 h-3.5" />
                      <span>{isFusing ? 'Fusing...' : 'Fuse into Inventory'}</span>
                    </button>
                  </div>

                  {/* Fusion Success Banner */}
                  {fusionResults && (
                    <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs space-y-1">
                      <div className="flex items-center space-x-2 text-emerald-400 font-bold">
                        <CheckCircle2 className="w-4 h-4" />
                        <span>Inventory Ledger Successfully Updated!</span>
                      </div>
                      <p className="text-[11px] text-slate-300">
                        Reconciled {fusionResults.length} catalog SKU(s) with new visible shelf observations.
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      ) : (
        /* CCTV VIDEO INGESTION SUB-TAB */
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left Column: Video Controls */}
            <div className="lg:col-span-5 space-y-4">
              <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                    <Video className="w-4 h-4 text-emerald-400" />
                    <span>CCTV Feed Video Input</span>
                  </h3>
                  <button
                    type="button"
                    onClick={handleLoadSampleVideo}
                    className="px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 transition flex items-center space-x-1"
                  >
                    <Sparkles className="w-3 h-3 text-emerald-400" />
                    <span>Use Sample Video</span>
                  </button>
                </div>

                {/* Video Dropzone */}
                <div
                  onClick={() => videoInputRef.current?.click()}
                  className="border-2 border-dashed border-slate-700 hover:border-emerald-500/50 rounded-2xl p-6 text-center cursor-pointer transition bg-slate-950/40 hover:bg-slate-900/40 group"
                >
                  <input
                    ref={videoInputRef}
                    type="file"
                    accept="video/mp4,video/avi,video/mov,video/webm"
                    className="hidden"
                    onChange={handleVideoFileChange}
                  />
                  <FileVideo className="w-10 h-10 text-slate-500 group-hover:text-emerald-400 mx-auto mb-2 transition" />
                  <p className="text-xs font-semibold text-slate-200">
                    {videoFile ? videoFile.name : 'Select or drop CCTV video recording'}
                  </p>
                  <p className="text-[11px] text-slate-500 mt-1">Supports MP4, AVI, WEBM (Max 200MB)</p>
                </div>

                {/* Sampling Parameters */}
                <div className="space-y-3">
                  <div>
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="font-semibold text-slate-300">Sampling Interval (sec)</span>
                      <span className="font-mono text-emerald-400 font-bold">{sampleInterval}s</span>
                    </div>
                    <input
                      type="range"
                      min="1"
                      max="15"
                      step="1"
                      value={sampleInterval}
                      onChange={(e) => setSampleInterval(parseFloat(e.target.value) || 3)}
                      className="w-full accent-emerald-500 cursor-pointer"
                    />
                    <span className="text-[10px] text-slate-500">
                      Extracts & inspects 1 frame every {sampleInterval} seconds.
                    </span>
                  </div>

                  <div>
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="font-semibold text-slate-300">Max Sampled Frames</span>
                      <span className="font-mono text-emerald-400 font-bold">{maxFrames}</span>
                    </div>
                    <input
                      type="range"
                      min="5"
                      max="50"
                      step="5"
                      value={maxFrames}
                      onChange={(e) => setMaxFrames(parseInt(e.target.value) || 20)}
                      className="w-full accent-emerald-500 cursor-pointer"
                    />
                  </div>
                </div>

                {/* Action Button */}
                <button
                  id="run-cctv-analysis-btn"
                  onClick={handleRunVideoAnalysis}
                  disabled={!videoFile || isVideoLoading}
                  className="w-full py-2.5 rounded-xl text-xs font-bold bg-emerald-500 hover:bg-emerald-400 text-slate-950 transition shadow-lg shadow-emerald-500/20 active:scale-95 disabled:opacity-50 flex items-center justify-center space-x-2"
                >
                  <Clock className={`w-4 h-4 ${isVideoLoading ? 'animate-spin' : ''}`} />
                  <span>{isVideoLoading ? 'Sampling & Analyzing Video...' : 'Run CCTV Analysis'}</span>
                </button>
              </div>

              {/* Video Player Preview */}
              {videoPreviewUrl && (
                <div className="glass-panel p-4 rounded-2xl border border-slate-800 space-y-2">
                  <div className="flex items-center space-x-2 text-xs font-bold text-slate-300">
                    <Play className="w-3.5 h-3.5 text-emerald-400" />
                    <span>Source Video Playback</span>
                  </div>
                  <video
                    src={videoPreviewUrl}
                    controls
                    className="w-full rounded-xl bg-black border border-slate-800 max-h-48 object-contain"
                  />
                </div>
              )}
            </div>

            {/* Right Column: Analysis Results */}
            <div className="lg:col-span-7 space-y-4">
              <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                    <Layers className="w-4 h-4 text-emerald-400" />
                    <span>CCTV Analysis & Peak Shelf Facings</span>
                  </h3>
                  {videoResult && (
                    <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold">
                      {videoResult.frames_sampled} frames inspected
                    </span>
                  )}
                </div>

                {videoResult ? (
                  <div className="space-y-4">
                    {/* Metrics Banner */}
                    <div className="grid grid-cols-3 gap-3">
                      <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 text-center">
                        <span className="text-[10px] uppercase font-bold text-slate-400">Duration</span>
                        <p className="text-base font-extrabold text-white mt-0.5">
                          {videoResult.video_duration_sec}s
                        </p>
                      </div>
                      <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 text-center">
                        <span className="text-[10px] uppercase font-bold text-slate-400">Sampled Frames</span>
                        <p className="text-base font-extrabold text-emerald-400 mt-0.5">
                          {videoResult.frames_sampled}
                        </p>
                      </div>
                      <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 text-center">
                        <span className="text-[10px] uppercase font-bold text-slate-400">Peak Facings</span>
                        <p className="text-base font-extrabold text-white mt-0.5">
                          {videoResult.aggregated_total}
                        </p>
                      </div>
                    </div>

                    {/* Peak Visible Breakdown & Fusion Button */}
                    <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                      <div>
                        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                          Peak Visible Shelf Observations
                        </h4>
                        <div className="flex flex-wrap gap-2 mt-2">
                          {Object.entries(videoResult.aggregated_counts).length > 0 ? (
                            Object.entries(videoResult.aggregated_counts).map(([cls, cnt]) => (
                              <span
                                key={cls}
                                className="px-2.5 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold"
                              >
                                {cls}: <span className="font-bold text-white">{cnt}</span>
                              </span>
                            ))
                          ) : (
                            <span className="text-xs text-slate-400">
                              No product items detected across video frames.
                            </span>
                          )}
                        </div>
                      </div>

                      <button
                        id="fuse-cctv-into-inventory-btn"
                        onClick={handleFuseCctvIntoInventory}
                        disabled={isCctvFusing || Object.keys(videoResult.aggregated_counts).length === 0}
                        className="px-4 py-2 rounded-xl text-xs font-bold bg-emerald-500 hover:bg-emerald-400 text-slate-950 transition shadow-md shadow-emerald-500/20 active:scale-95 disabled:opacity-50 flex items-center space-x-1.5 flex-shrink-0"
                      >
                        <Layers className="w-3.5 h-3.5" />
                        <span>{isCctvFusing ? 'Fusing...' : 'Fuse into Inventory'}</span>
                      </button>
                    </div>

                    {/* CCTV Fusion Success Banner */}
                    {cctvFusionResults && (
                      <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs space-y-1">
                        <div className="flex items-center space-x-2 text-emerald-400 font-bold">
                          <CheckCircle2 className="w-4 h-4" />
                          <span>CCTV Observations Reconciled into Inventory Ledger!</span>
                        </div>
                        <p className="text-[11px] text-slate-300">
                          Updated {cctvFusionResults.length} catalog SKU(s) using peak shelf observations.
                        </p>
                      </div>
                    )}

                    {/* Sampled Keyframes Gallery */}
                    {videoResult.frame_results && videoResult.frame_results.length > 0 && (
                      <div className="space-y-3">
                        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center justify-between">
                          <span>Sampled Frame Timeline</span>
                          <span className="text-[11px] text-slate-500 normal-case">
                            Click any frame to inspect visual bounding boxes
                          </span>
                        </h4>

                        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                          {videoResult.frame_results.map((frame, idx) => (
                            <div
                              key={idx}
                              onClick={() => setSelectedFrame(frame)}
                              className={`rounded-xl border p-2 cursor-pointer transition ${
                                selectedFrame?.frame_index === frame.frame_index
                                  ? 'border-emerald-500 bg-emerald-500/10'
                                  : 'border-slate-800 bg-slate-900/60 hover:border-slate-700'
                              }`}
                            >
                              <div className="relative rounded-lg overflow-hidden bg-black aspect-video flex items-center justify-center">
                                {frame.annotated_frame_url ? (
                                  <img
                                    src={frame.annotated_frame_url}
                                    alt={`Frame ${frame.frame_index}`}
                                    className="w-full h-full object-cover"
                                  />
                                ) : (
                                  <div className="text-[10px] text-slate-500">Frame #{frame.frame_index}</div>
                                )}
                                <span className="absolute bottom-1 right-1 px-1.5 py-0.5 rounded bg-black/70 text-[9px] font-mono text-white">
                                  {frame.timestamp_label || `${frame.timestamp_sec}s`}
                                </span>
                              </div>
                              <div className="mt-1.5 flex items-center justify-between text-[11px]">
                                <span className="text-slate-400 font-medium">Items</span>
                                <span className="text-emerald-400 font-bold">{frame.total_detected}</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Selected Frame Full Inspector */}
                    {selectedFrame && selectedFrame.annotated_frame_url && (
                      <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-white flex items-center space-x-2">
                            <Eye className="w-3.5 h-3.5 text-emerald-400" />
                            <span>Frame Inspection: {selectedFrame.timestamp_label} ({selectedFrame.timestamp_sec}s)</span>
                          </span>
                          <span className="text-[11px] text-slate-400">
                            {selectedFrame.total_detected} detections
                          </span>
                        </div>
                        <div className="rounded-xl overflow-hidden border border-slate-800 bg-black flex items-center justify-center max-h-[380px]">
                          <img
                            src={selectedFrame.annotated_frame_url}
                            alt="Annotated Frame"
                            className="w-full object-contain"
                          />
                        </div>
                      </div>
                    )}

                    {/* Operational Caveat */}
                    <p className="text-[10px] text-slate-500 italic p-3 rounded-xl bg-slate-900/40 border border-slate-800/60">
                      ℹ️ {videoResult.caveat}
                    </p>
                  </div>
                ) : (
                  <div className="text-center py-16 text-slate-500">
                    <Video className="w-12 h-12 mx-auto mb-2 opacity-30" />
                    <p className="text-xs font-medium text-slate-400">No video analysis completed yet</p>
                    <p className="text-[11px] text-slate-600 mt-1">
                      Upload a CCTV recording or click &ldquo;Use Sample Video&rdquo; to begin.
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
