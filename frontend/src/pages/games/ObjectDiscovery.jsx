import GenericGame from "../../components/GenericGame";

export default function ObjectDiscovery() {
  return (
    <GenericGame
      gameCode="object_discovery"
      gameName="Object Discovery"
      gameIcon="🔍"
      trialCount={8}
      multiSelect={true}
    />
  );
}
