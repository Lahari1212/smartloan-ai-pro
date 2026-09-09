const stages = [
  "Application created",
  "Document uploaded",
  "Document classified",
  "Document validated",
  "Eligibility calculated",
];

export default function VerificationTimeline({ currentStage = 0 }) {
  return (
    <section className="panel">
      <div className="section-heading">
        <h2>AI processing timeline</h2>
        <p>Track the document processing workflow.</p>
      </div>

      <div className="timeline">
        {stages.map((stage, index) => {
          const completed = index <= currentStage;

          return (
            <div className="timeline-item" key={stage}>
              <div
                className={`timeline-circle ${
                  completed ? "completed" : ""
                }`}
              >
                {completed ? "✓" : index + 1}
              </div>

              <p className={completed ? "completed-text" : ""}>
                {stage}
              </p>
            </div>
          );
        })}
      </div>
    </section>
  );
}