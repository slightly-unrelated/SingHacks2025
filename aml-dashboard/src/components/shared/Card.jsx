const Card = ({ title, children, className = '' }) => {
  return (
    <div className={`card ${className}`}>
      {title && (
        <h3 className="text-lg font-semibold text-text-primary mb-4">
          {title}
        </h3>
      )}
      {children}
    </div>
  );
};

export default Card;
