import { useMemo, useState, useEffect } from "react";

const EXT_TRY = ["png", "jpg", "jpeg", "webp"];

export default function OptionCard({ option, onClick, disabled, highlight }) {
  // option can be string "cat" OR object {id,label,image_url}
  const id = typeof option === "string" ? option : option?.id;
  const label = typeof option === "string" ? option : option?.label || option?.id || "";

  const cls = [
    "card",
    disabled ? "cardDisabled" : "",
    highlight ? "cardHighlight" : "",
  ]
    .filter(Boolean)
    .join(" ");

  // Build candidate image URLs:
  // 1) if backend provides image_url, try it first
  // 2) fallback to /ja/<id>.<ext> for png/jpg/jpeg/webp
  const candidates = useMemo(() => {
    const backendImg =
      typeof option === "object" && (option?.image_url || option?.image)
        ? [option.image_url || option.image]
        : [];
    const rest = id ? EXT_TRY.map((ext) => `/ja/${id}.${ext}`) : [];
    return [...backendImg, ...rest];
  }, [option, id]);

  const [idx, setIdx] = useState(0);
  const [imgOk, setImgOk] = useState(true);

  // reset idx when option changes
  useEffect(() => {
    setIdx(0);
    setImgOk(true);
  }, [id]);

  const src = candidates[idx] || "";

  return (
    <div className={cls} onClick={() => !disabled && onClick(option)}>
      {src && imgOk ? (
        <div className="cardMedia">
          <img
            src={src}
            alt={label}
            draggable={false}
            onError={() => {
              if (idx < candidates.length - 1) {
                setIdx((v) => v + 1);
              } else {
                setImgOk(false);
              }
            }}
          />
        </div>
      ) : null}

      <div className="cardLabel">{label}</div>
    </div>
  );
}
