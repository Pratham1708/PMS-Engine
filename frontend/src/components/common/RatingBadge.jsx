const ratingClassMap = {
  'STRONG BUY': 'strong-buy',
  'BUY': 'buy',
  'HOLD': 'hold',
  'SELL': 'sell',
  'STRONG SELL': 'strong-sell',
};

export default function RatingBadge({ rating, large }) {
  const cls = ratingClassMap[rating] || 'hold';
  return (
    <span className={`rating-badge ${cls} ${large ? 'rating-badge-lg' : ''}`}>
      {rating}
    </span>
  );
}
