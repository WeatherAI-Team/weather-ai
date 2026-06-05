"use client";
import { useState, useRef, useEffect, useCallback } from "react";
import Hls from "hls.js";
import styles from "./page.module.css";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:5000";
const API_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:5000";

type TabType = "cctv" | "upload";

type Detection = {
  bbox: [number, number, number, number];
  label: string;
  confidence: number;
};

type Result = {
  detected: boolean;
  confidence: number;
  label: string;
  detections: Detection[];
  annotated_url?: string;
};

type CctvItem = {
  cctvname: string;
  cctvurl: string;
  cctvformat: string;
  coordx: number;
  coordy: number;
};

type DetectInfo = {
  weather: string;
  confidence: number;
  hasDangerVehicle: boolean;
  is_danger: boolean;
};

const REGIONS = [
  { label: "전체", keywords: [] },
  { label: "서울", keywords: ["서울"] },
  {
    label: "경기",
    keywords: [
      "경기",
      "수원",
      "성남",
      "안양",
      "부천",
      "평택",
      "안산",
      "고양",
      "용인",
      "파주",
      "시흥",
      "김포",
      "화성",
      "양주",
      "포천",
    ],
  },
  { label: "인천", keywords: ["인천"] },
  {
    label: "강원",
    keywords: ["강원", "춘천", "원주", "강릉", "동해", "태백", "속초", "삼척"],
  },
  {
    label: "충청",
    keywords: [
      "충북",
      "충남",
      "충청",
      "대전",
      "세종",
      "청주",
      "천안",
      "공주",
      "아산",
      "서산",
      "논산",
    ],
  },
  {
    label: "전북",
    keywords: ["전북", "전주", "군산", "익산", "정읍", "남원", "김제"],
  },
  { label: "전남", keywords: ["전남", "목포", "여수", "순천", "나주", "광양"] },
  { label: "광주", keywords: ["광주"] },
  {
    label: "경북",
    keywords: ["경북", "포항", "경주", "김천", "안동", "구미", "영주"],
  },
  {
    label: "경남",
    keywords: [
      "경남",
      "창원",
      "진주",
      "통영",
      "사천",
      "김해",
      "밀양",
      "거제",
      "양산",
    ],
  },
  { label: "대구", keywords: ["대구"] },
  { label: "울산", keywords: ["울산"] },
  { label: "부산", keywords: ["부산"] },
  { label: "제주", keywords: ["제주"] },
];

function getRegion(cctvname: string): string {
  for (const r of REGIONS.slice(1)) {
    if (r.keywords.some((kw) => cctvname.includes(kw))) return r.label;
  }
  return "기타";
}

// ── 바운딩박스 오버레이 컴포넌트 ──
function BoundingBoxOverlay({
  src,
  detections,
}: {
  src: string;
  detections: Detection[];
}) {
  const imgRef = useRef<HTMLImageElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const draw = useCallback(() => {
    const img = imgRef.current;
    const canvas = canvasRef.current;
    if (!img || !canvas) return;

    canvas.width = img.offsetWidth;
    canvas.height = img.offsetHeight;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    detections.forEach((det) => {
      const [x1, y1, x2, y2] = det.bbox;
      const x = x1 * canvas.width;
      const y = y1 * canvas.height;
      const w = (x2 - x1) * canvas.width;
      const h = (y2 - y1) * canvas.height;
      const color = det.confidence >= 0.85 ? "#e74c3c" : "#f39c12";

      ctx.strokeStyle = color;
      ctx.lineWidth = 2.5;
      ctx.shadowColor = color;
      ctx.shadowBlur = 4;
      ctx.strokeRect(x, y, w, h);
      ctx.shadowBlur = 0;

      const text = `${det.label}  ${(det.confidence * 100).toFixed(1)}%`;
      ctx.font = "bold 12px sans-serif";
      const tw = ctx.measureText(text).width;
      const labelY = y > 26 ? y - 24 : y + h + 2;
      ctx.fillStyle = color;
      ctx.fillRect(x - 1, labelY, tw + 12, 22);

      ctx.fillStyle = "#fff";
      ctx.fillText(text, x + 5, labelY + 15);
    });
  }, [detections]);

  useEffect(() => {
    draw();
  }, [draw]);

  return (
    <div className={styles.bboxContainer}>
      <img
        ref={imgRef}
        src={src}
        alt="분석 이미지"
        className={styles.bboxImage}
        onLoad={draw}
      />
      <canvas ref={canvasRef} className={styles.bboxCanvas} />
    </div>
  );
}

// ── HLS 플레이어 + AI 바운딩박스 컴포넌트 ──
function HlsPlayer({
  src,
  className,
  onDetect,
  onUrlExpired,
  onSaveDetection,
  monitoringEnabled = false,
}: {
  src: string;
  className?: string;
  onDetect?: (info: DetectInfo | null) => void;
  onUrlExpired?: () => void;
  onSaveDetection?: (aiData: any) => void;
  monitoringEnabled?: boolean;
}) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const overlayRef = useRef<HTMLCanvasElement>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const isAnalyzingRef = useRef(false);
  const lastSaveAtRef = useRef(0);

  // ── HLS 스트리밍 연결 ──
  useEffect(() => {
    const video = videoRef.current;
    if (!video || !src) return;

    let hls: Hls | null = null;

    if (Hls.isSupported()) {
      hls = new Hls();
      hls.loadSource(src);
      hls.attachMedia(video);
      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        video.play().catch(() => {});
      });
      // ✅ URL 만료(403) 감지
      hls.on(Hls.Events.ERROR, (_event, data) => {
        if (data.fatal && data.type === Hls.ErrorTypes.NETWORK_ERROR) {
          onUrlExpired?.();
        }
      });
    } else if (video.canPlayType("application/vnd.apple.mpegurl")) {
      video.src = src;
      video.play().catch(() => {});
    }

    return () => {
      hls?.destroy();
    };
  }, [src]);

  // ── 프레임 캡처 → AI 서버 전송 → 바운딩박스 그리기 ──
  useEffect(() => {
    const video = videoRef.current;
    const captureCanvas = canvasRef.current;
    const overlay = overlayRef.current;
    if (!video || !captureCanvas || !overlay) return;

    // ✅ AbortController: CCTV 전환 시 진행 중인 fetch 중단
    const abortController = new AbortController();

    const analyzeFrame = async () => {
      if (!monitoringEnabled) {
        onDetect?.(null);
        return;
      }

      if (isAnalyzingRef.current) return;
      if (video.readyState < 2 || video.paused) return;

      isAnalyzingRef.current = true;

      try {
        captureCanvas.width = 640;
        captureCanvas.height = 360;
        const ctx = captureCanvas.getContext("2d");
        if (!ctx) {
          isAnalyzingRef.current = false;
          return;
        }
        ctx.drawImage(video, 0, 0, captureCanvas.width, captureCanvas.height);

        captureCanvas.toBlob(
          async (blob) => {
            // ✅ abort됐거나 blob 없으면 즉시 종료
            if (!blob || abortController.signal.aborted) {
              isAnalyzingRef.current = false;
              return;
            }

            try {
              const formData = new FormData();
              formData.append("file", blob, "frame.jpg");

              const res = await fetch(`${API_URL}/api/ai/detect`, {
                method: "POST",
                body: formData,
                signal: abortController.signal, // ✅ fetch에 signal 연결
              });

              // ✅ 응답 왔어도 이미 전환됐으면 무시
              if (abortController.signal.aborted) {
                isAnalyzingRef.current = false;
                return;
              }

              const data = await res.json();

              overlay.width = video.offsetWidth;
              overlay.height = video.offsetHeight;
              const octx = overlay.getContext("2d");
              if (!octx) {
                isAnalyzingRef.current = false;
                return;
              }
              octx.clearRect(0, 0, overlay.width, overlay.height);

              if (data.success) {
                const hasDangerVehicle = !!(
                  data.yolo_boxes && data.yolo_boxes.length > 0
                );

                onDetect?.({
                  weather: data.weather,
                  confidence: data.confidence,
                  hasDangerVehicle,
                  is_danger: data.is_danger,
                });

                const now = Date.now();

                const shouldSave =
                  data.is_danger &&
                  hasDangerVehicle &&
                  now - lastSaveAtRef.current > 60_000;

                if (shouldSave) {
                  lastSaveAtRef.current = now;
                  onSaveDetection?.(data);
                }

                if (data.yolo_boxes && data.yolo_boxes.length > 0) {
                  data.yolo_boxes.forEach((box: any) => {
                    const [x1, y1, x2, y2] = box.box_coords;
                    const scaleX = overlay.width / captureCanvas.width;
                    const scaleY = overlay.height / captureCanvas.height;

                    const x = x1 * scaleX;
                    const y = y1 * scaleY;
                    const w = (x2 - x1) * scaleX;
                    const h = (y2 - y1) * scaleY;

                    octx.strokeStyle = "#e74c3c";
                    octx.lineWidth = 2.5;
                    octx.shadowColor = "#e74c3c";
                    octx.shadowBlur = 4;
                    octx.strokeRect(x, y, w, h);
                    octx.shadowBlur = 0;

                    const text = `${box.class_name} ${box.confidence}%`;
                    octx.font = "bold 13px sans-serif";
                    const tw = octx.measureText(text).width;
                    octx.fillStyle = "#e74c3c";
                    octx.fillRect(x, y - 24, tw + 12, 22);
                    octx.fillStyle = "#fff";
                    octx.fillText(text, x + 6, y - 7);
                  });
                }
              }
            } catch (e: any) {
              // ✅ AbortError는 정상 동작이므로 로그 생략
              if (e.name !== "AbortError") {
                console.error("AI 분석 실패:", e);
              }
            } finally {
              isAnalyzingRef.current = false;
            }
          },
          "image/jpeg",
          0.8,
        );
      } catch (e) {
        console.error("프레임 캡처 실패:", e);
        isAnalyzingRef.current = false;
      }
    };

    intervalRef.current = setInterval(analyzeFrame, 500);

    return () => {
      // ✅ CCTV 전환 시 정리
      if (intervalRef.current) clearInterval(intervalRef.current);
      abortController.abort(); // 진행 중인 fetch 중단
      isAnalyzingRef.current = false; // 분석 플래그 초기화
    };
  }, [src, monitoringEnabled]);

  return (
    <div style={{ position: "relative", width: "100%" }}>
      <video
        ref={videoRef}
        className={className}
        autoPlay
        muted
        playsInline
        controls
      />
      <canvas ref={canvasRef} style={{ display: "none" }} />
      <canvas
        ref={overlayRef}
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: "100%",
          height: "100%",
          pointerEvents: "none",
        }}
      />
    </div>
  );
}

// ── 메인 페이지 ──
export default function AiPage() {
  useEffect(() => {
    document.title = "Weather AI - AI 탐지";
  }, []);
  const getAuthToken = () => {
    const directToken =
      localStorage.getItem("access_token") ||
      localStorage.getItem("token") ||
      localStorage.getItem("accessToken") ||
      localStorage.getItem("authToken");

    if (directToken) return directToken;

    const getTokenFromJson = (key: string) => {
      try {
        const obj = JSON.parse(localStorage.getItem(key) || "null");

        return (
          obj?.access_token ||
          obj?.accessToken ||
          obj?.token ||
          obj?.authToken ||
          obj?.jwt ||
          obj?.data?.access_token ||
          obj?.data?.accessToken ||
          obj?.data?.token ||
          null
        );
      } catch {
        return null;
      }
    };

    return getTokenFromJson("loginUser") || getTokenFromJson("user");
  };
  const [tab, setTab] = useState<TabType>("cctv");
  const [selectedCctv, setSelectedCctv] = useState<number | null>(null);
  const [cctvList, setCctvList] = useState<CctvItem[]>([]);
  const [cctvLoading, setCctvLoading] = useState(false);
  const [selectedRegion, setSelectedRegion] = useState("전체");
  const [detectInfo, setDetectInfo] = useState<DetectInfo | null>(null);

  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<Result | null>(null);
  const [uploadedUrl, setUploadedUrl] = useState<string | null>(null);
  const [isImage, setIsImage] = useState(false);

  const [cctvGate, setCctvGate] = useState<any>(null);
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    const token = getAuthToken();

    console.log("[Auth token exists]", !!token);

    if (!token) {
      setIsAdmin(false);
      return;
    }

    try {
      const payload = JSON.parse(atob(token.split(".")[1]));

      console.log("[Auth payload]", payload);

      setIsAdmin(payload.role === "admin");
    } catch (e) {
      console.error("토큰 role 확인 실패:", e);
      setIsAdmin(false);
    }
  }, []);

  useEffect(() => {
    setDetectInfo(null);
  }, [selectedCctv]);

  // ── CCTV 목록 불러오기 ──
  const fetchCctvList = useCallback(async () => {
    setCctvLoading(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/cctv`);
      const data = await res.json();
      const items: CctvItem[] = data?.response?.data ?? [];
      setCctvList(items);
    } catch (err) {
      console.error("CCTV 목록 불러오기 실패:", err);
    } finally {
      setCctvLoading(false);
    }
  }, []);

  useEffect(() => {
    if (tab !== "cctv") return;
    fetchCctvList();
  }, [tab]);

  useEffect(() => {
    if (tab !== "cctv") return;

    const fetchCctvGate = async () => {
      const token = getAuthToken();

      console.log("[CCTV Gate] isAdmin:", isAdmin);
      console.log("[CCTV Gate] token exists:", !!token);

      if (!token || !isAdmin) {
        setCctvGate(null);
        return;
      }

      try {
        const res = await fetch(`${BACKEND_URL}/api/cctv/gate`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        console.log("[CCTV Gate status]", res.status);

        const data = await res.json();
        console.log("[CCTV Gate response]", data);

        if (res.status === 401 || res.status === 403) {
          setCctvGate(null);
          console.warn("CCTV Gate는 관리자만 조회할 수 있습니다.");
          return;
        }

        if (data.success) {
          setCctvGate(data.data);
          console.log("[CCTV Gate]", data.data);
        }
      } catch (e) {
        console.error("CCTV Gate 조회 실패:", e);
      }
    };

    fetchCctvGate();

    const timer = setInterval(fetchCctvGate, 10 * 60 * 1000);

    return () => clearInterval(timer);
  }, [tab, isAdmin]);

  // ✅ URL 만료 시 목록 갱신 (실패할 때만 1번 호출 → API 절약)
  const handleUrlExpired = useCallback(() => {
    if (cctvLoading) return;
    console.log("[CCTV] URL 만료 감지 → 목록 갱신");
    fetchCctvList();
  }, [cctvLoading, fetchCctvList]);

  const saveDetectionEvent = useCallback(
    async (aiData: any) => {
      if (selectedCctv === null) return;

      const cam = cctvList[selectedCctv];
      if (!cam) return;

      try {
        const res = await fetch(`${BACKEND_URL}/api/detections/save-result`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            ai_result: aiData,
            cctv_source_id: null,
            cctv_name: cam.cctvname,
            latitude: cam.coordy,
            longitude: cam.coordx,
            image_url: null,
          }),
        });

        const result = await res.json();
        console.log("[DB 저장 결과]", result);
      } catch (e) {
        console.error("탐지 이벤트 저장 실패:", e);
      }
    },
    [selectedCctv, cctvList],
  );

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const fileIsImage = file.type.startsWith("image/");
    setIsImage(fileIsImage);
    setUploading(true);
    setResult(null);
    setUploadedUrl(URL.createObjectURL(file));

    const formData = new FormData();
    formData.append("file", file);
    formData.append("user_id", "1");
    formData.append("original_filename", file.name);

    const endpoint = fileIsImage ? "/api/ai/detect" : "/api/detections/analyze";

    try {
      const res = await fetch(`${BACKEND_URL}${endpoint}`, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();

      const aiResult = fileIsImage ? data : (data?.data?.ai_result ?? data);
      const detectedVehicleName =
        typeof aiResult.detected_vehicle === "string"
          ? aiResult.detected_vehicle.split(" ")[0]
          : null;

      const detectedVehicleConfidenceMatch =
        typeof aiResult.detected_vehicle === "string"
          ? aiResult.detected_vehicle.match(/\(([\d.]+)%\)/)
          : null;

      const detectedVehicleConfidence = detectedVehicleConfidenceMatch
        ? Number(detectedVehicleConfidenceMatch[1])
        : (aiResult.danger_confidence ?? 0);

      if (data.success && aiResult) {
        const yoloBoxes =
          aiResult.yolo_boxes ??
          aiResult.detections?.map((det: any) => ({
            class_name: det.label,
            confidence:
              det.confidence > 1
                ? det.confidence
                : Number((det.confidence * 100).toFixed(1)),
            box_coords: det.bbox,
          })) ??
          (detectedVehicleName
            ? [
                {
                  class_name: detectedVehicleName,
                  confidence: detectedVehicleConfidence,
                  box_coords: null,
                },
              ]
            : []);
        const uniqueYoloBoxes = Object.values(
          yoloBoxes.reduce((acc: Record<string, any>, box: any) => {
            const key = box.class_name;

            if (!acc[key] || box.confidence > acc[key].confidence) {
              acc[key] = box;
            }

            return acc;
          }, {}),
        );

        setResult({
          detected: Boolean(aiResult.is_danger || aiResult.has_danger_car),
          confidence: aiResult.confidence ?? 0,
          label: aiResult.weather ?? "UNKNOWN",
          detections:
            aiResult.detections ??
            uniqueYoloBoxes.map((box: any) => ({
              bbox: box.box_coords,
              label: box.class_name,
              confidence:
                box.confidence > 1 ? box.confidence / 100 : box.confidence,
            })),
          annotated_url: aiResult.annotated_path
            ? `http://localhost:8000/${aiResult.annotated_path}`
            : undefined,  // 추가
        });

        const shouldSave =
          fileIsImage &&
          (aiResult.is_danger ||
            aiResult.has_danger_car ||
            yoloBoxes.length > 0);

        if (shouldSave) {
          const saveRes = await fetch(
            `${BACKEND_URL}/api/detections/save-result`,
            {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
              },
              body: JSON.stringify({
                ai_result: {
                  ...aiResult,
                  yolo_boxes: uniqueYoloBoxes,
                },
                cctv_source_id: null,
                cctv_name: fileIsImage ? "업로드 이미지" : "업로드 영상",
                latitude: null,
                longitude: null,
                image_url:
                  aiResult.file_url ??
                  aiResult.video_url ??
                  aiResult.local_path ??
                  null,
              }),
            },
          );

          const saveResult = await saveRes.json();
          console.log("[업로드 분석 DB 저장 결과]", saveResult);
        }
      }
    } catch {
      setResult({
        detected: false,
        confidence: 0,
        label: "분석 실패",
        detections: [],
      });
    } finally {
      setUploading(false);
    }
  };

  const handleReset = () => {
    setUploadedUrl(null);
    setResult(null);
    setIsImage(false);
  };

  const selected = selectedCctv !== null ? cctvList[selectedCctv] : null;

  return (
    <div className={styles.page}>
      <section className={styles.hero}>
        <div className="container">
          <p className={styles.eyebrow}>AI 탐지</p>
          <h1 className={styles.title}>위험 차량 탐지</h1>
          <p className={styles.desc}>
            연동된 CCTV 실시간 영상을 분석하거나, 영상 파일을 업로드하여 AI
            분석을 시작하세요
          </p>
        </div>
      </section>

      <section className={styles.main}>
        <div className="container">
          <div className={styles.tabBar}>
            <button
              className={`${styles.tabBtn} ${tab === "cctv" ? styles.tabActive : ""}`}
              onClick={() => setTab("cctv")}
            >
              📡 CCTV 실시간
            </button>
            <button
              className={`${styles.tabBtn} ${tab === "upload" ? styles.tabActive : ""}`}
              onClick={() => setTab("upload")}
            >
              📁 영상 업로드
            </button>
          </div>

          {tab === "cctv" && (
            <div className={styles.cctvTabGrid}>
              <div className={styles.panel}>
                <h2>{selected ? selected.cctvname : "CCTV 실시간 화면"}</h2>
                {isAdmin && tab === "cctv" && cctvGate && (
                  <div
                    className={`${styles.gateCard} ${
                      cctvGate.monitoring_required
                        ? styles.gateActive
                        : styles.gateIdle
                    }`}
                  >
                    <div className={styles.gateLeft}>
                      <span className={styles.gateIcon}>
                        {cctvGate.monitoring_required ? "🟢" : "⏸️"}
                      </span>

                      <div>
                        <p className={styles.gateLabel}>LLM Gate</p>
                        <strong className={styles.gateTitle}>
                          CCTV AI 감시{" "}
                          {cctvGate.monitoring_required ? "활성화" : "대기"}
                        </strong>
                      </div>
                    </div>

                    <div className={styles.gateRight}>
                      <span className={styles.gateBadge}>
                        {cctvGate.risk_level}
                      </span>
                      <span
                        className={styles.gateReason}
                        title={cctvGate.reason}
                      >
                        {cctvGate.monitoring_required
                          ? "위험 기상 조건 확인됨"
                          : "현재 감시 대기 상태"}
                      </span>
                    </div>
                  </div>
                )}

                {isAdmin && selected && detectInfo && (
                  <div className={styles.cctvDetectBar}>
                    <span
                      style={{
                        color: detectInfo.is_danger ? "#e74c3c" : "#20436d",
                      }}
                    >
                      날씨: {detectInfo.weather} ({detectInfo.confidence}%)
                    </span>
                    <span
                      style={{
                        color: detectInfo.hasDangerVehicle
                          ? "#e74c3c"
                          : "#20436d",
                      }}
                    >
                      {detectInfo.hasDangerVehicle
                        ? "⚠️ 위험차량: 감지됨"
                        : "✅ 위험차량: 없음"}
                    </span>
                  </div>
                )}
                <div className={styles.cctvBox}>
                  {selected ? (
                    <HlsPlayer
                      key={selected.cctvurl}
                      src={`${BACKEND_URL}/api/cctv/stream?url=${encodeURIComponent(selected.cctvurl)}`}
                      className={styles.cctvStream}
                      onDetect={setDetectInfo}
                      onUrlExpired={handleUrlExpired}
                      onSaveDetection={saveDetectionEvent}
                      monitoringEnabled={
                        isAdmin && (cctvGate?.monitoring_required ?? false)
                      }
                    />
                  ) : (
                    <div className={styles.cctvEmpty}>
                      <span>📷</span>
                      <p>오른쪽 목록에서 CCTV를 선택하세요</p>
                    </div>
                  )}
                </div>
              </div>

              <div className={styles.panel}>
                <h2>연동 CCTV 목록</h2>
                <div className={styles.regionBar}>
                  {REGIONS.map((r) => (
                    <button
                      key={r.label}
                      className={`${styles.regionBtn} ${selectedRegion === r.label ? styles.regionActive : ""}`}
                      onClick={() => {
                        setSelectedRegion(r.label);
                        setSelectedCctv(null);
                      }}
                    >
                      {r.label}
                    </button>
                  ))}
                </div>
                <div className={styles.cctvHistory}>
                  {cctvLoading && <p>불러오는 중...</p>}
                  {!cctvLoading && cctvList.length === 0 && (
                    <p>CCTV 목록이 없습니다.</p>
                  )}
                  {!cctvLoading &&
                    (() => {
                      const filtered =
                        selectedRegion === "전체"
                          ? cctvList
                          : cctvList.filter(
                              (cam) =>
                                getRegion(cam.cctvname) === selectedRegion,
                            );
                      if (filtered.length === 0 && cctvList.length > 0) {
                        return (
                          <p className={styles.cctvEmpty2}>
                            해당 지역에 연동된 CCTV가 없습니다
                          </p>
                        );
                      }
                      return filtered.map((cam) => {
                        const origIdx = cctvList.indexOf(cam);
                        return (
                          <div
                            key={origIdx}
                            className={`${styles.cctvHistoryItem} ${selectedCctv === origIdx ? styles.cctvItemSelected : ""}`}
                            onClick={() => setSelectedCctv(origIdx)}
                          >
                            <span
                              className={`${styles.cctvDot} ${styles.dotWarn}`}
                            />
                            <div className={styles.cctvHistoryInfo}>
                              <p className={styles.cctvHistoryUrl}>
                                {cam.cctvname}
                              </p>
                              <p className={styles.cctvHistoryMeta}>
                                {cam.cctvformat} · {cam.coordx}, {cam.coordy}
                              </p>
                            </div>
                          </div>
                        );
                      });
                    })()}
                </div>
              </div>
            </div>
          )}

          {tab === "upload" && (
            <div className={styles.tabGrid}>
              <div className={styles.panel}>
                <h2>
                  {uploadedUrl
                    ? isImage
                      ? result?.detections?.length
                        ? "탐지 결과 (바운딩박스)"
                        : "업로드된 이미지"
                      : "업로드된 영상"
                    : "영상 업로드"}
                </h2>

                {uploadedUrl ? (
                  <div className={styles.videoPreview}>
                    {isImage ? (
                      result?.detections?.length ? (
                        <BoundingBoxOverlay
                          src={uploadedUrl}
                          detections={result.detections}
                        />
                      ) : (
                        <img
                          src={uploadedUrl}
                          alt="업로드된 이미지"
                          className={styles.uploadedImage}
                        />
                      )
                    ) : (
                      <video
                        src={result?.annotated_url || uploadedUrl}
                        controls
                        className={styles.videoPlayer}
                      />
                    )}
                    <button className={styles.resetBtn} onClick={handleReset}>
                      다시 업로드
                    </button>
                  </div>
                ) : (
                  <div className={styles.dropZone}>
                    <span className={styles.dropIcon}>📁</span>
                    <p>영상 또는 이미지 파일을 드래그하거나 클릭하여 업로드</p>
                    <span className={styles.dropHint}>
                      MP4, AVI, MOV, JPG, PNG · 최대 500MB
                    </span>
                    <input
                      type="file"
                      accept="video/*,image/*"
                      className={styles.fileInput}
                      onChange={handleUpload}
                    />
                  </div>
                )}
              </div>

              <div className={styles.panel}>
                <h2>분석 결과</h2>
                {uploading && (
                  <div className={styles.loading}>
                    <div className={styles.spinner} />
                    <p>AI 분석 중...</p>
                  </div>
                )}
                {result && !uploading && (
                  <>
                    <div
                      className={`${styles.result} ${result.detected ? styles.danger : styles.safe}`}
                    >
                      <div className={styles.resultIcon}>
                        {result.detected ? "⚠️" : "✅"}
                      </div>
                      <h3>
                        {result.detected
                          ? "위험 차량 탐지됨"
                          : "위험 차량 없음"}
                      </h3>
                      <p className={styles.resultLabel}>{result.label}</p>
                      <div className={styles.confidence}>
                        <span>신뢰도</span>
                        <div className={styles.bar}>
                          <div
                            className={styles.fill}
                            style={{ width: `${result.confidence}%` }}
                          />
                        </div>
                        <span>{result.confidence}%</span>
                      </div>
                    </div>

                    {result.detections.length > 0 && (
                      <div className={styles.detectionList}>
                        <p className={styles.detectionListTitle}>
                          탐지된 객체 ({result.detections.length}개)
                        </p>
                        {result.detections.map((det, i) => (
                          <div key={i} className={styles.detectionItem}>
                            <span className={styles.detectionIndex}>
                              {i + 1}
                            </span>
                            <span className={styles.detectionLabel}>
                              {det.label}
                            </span>
                            <div className={styles.detectionConf}>
                              <div className={styles.detectionConfBar}>
                                <div
                                  className={styles.detectionConfFill}
                                  style={{
                                    width: `${det.confidence * 100}%`,
                                    background:
                                      det.confidence >= 0.85
                                        ? "#e74c3c"
                                        : "#f39c12",
                                  }}
                                />
                              </div>
                              <span>{(det.confidence * 100).toFixed(1)}%</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </>
                )}
                {!result && !uploading && (
                  <div className={styles.placeholder}>
                    <span>📷</span>
                    <p>
                      영상 또는 이미지를 업로드하면
                      <br />
                      분석 결과가 표시됩니다
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
