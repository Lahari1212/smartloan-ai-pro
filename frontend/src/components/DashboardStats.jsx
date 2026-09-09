export default function DashboardStats({ applications }) {
  const stats = [
    {
      label: "Total Applications",
      value: applications.length,
    },
    {
      label: "Eligible",
      value: applications.filter(
        (item) => item.status === "Eligible"
      ).length,
    },
    {
      label: "Manual Review",
      value: applications.filter(
        (item) => item.status === "Manual Review"
      ).length,
    },
    {
      label: "Pending",
      value: applications.filter(
        (item) => item.status === "Document Pending"
      ).length,
    },
  ];

  return (
    <div className="stats-grid">
      {stats.map((stat) => (
        <div className="stat-card" key={stat.label}>
          <p>{stat.label}</p>
          <h3>{stat.value}</h3>
        </div>
      ))}
    </div>
  );
}