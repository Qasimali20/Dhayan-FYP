import GenericGame from "../../components/GenericGame";

export default function ProblemSolving() {
  return (
    <GenericGame
      gameCode="problem_solving"
      gameName="Problem Solving"
      gameIcon="🧩"
      trialCount={8}
      multiSelect={false}
    />
  );
}
