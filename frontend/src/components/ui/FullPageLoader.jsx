export function FullPageLoader({ label = "Loading..." }) {
  return (
    <div className="fullpage-loader">
      <div className="spinner" />
      <p>{label}</p>
    </div>
  );
}