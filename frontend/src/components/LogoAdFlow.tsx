export function LogoAdFlow({ size = 22 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden="true"
    >
      <path
        d="M12 3.2L4.2 18.8H8.3L12 11.1L15.7 18.8H19.8L12 3.2Z"
        fill="currentColor"
      />
      <path
        d="M7.6 15.2C9.4 13.7 11.2 13.2 13.2 13.8C14.7 14.2 16.2 13.9 17.8 12.6"
        stroke="#a5f3eb"
        strokeWidth="2.1"
        strokeLinecap="round"
      />
      <circle cx="18.2" cy="6.2" r="1.9" fill="#a5f3eb" />
    </svg>
  );
}
