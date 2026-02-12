import { useAppStore } from './stores/useAppStore';
import HomeScreen from './screens/HomeScreen';
import LoadingScreen from './screens/LoadingScreen';
import ResultsScreen from './screens/ResultsScreen';
import MapScreen from './screens/MapScreen';
import IdleTimer from './components/IdleTimer';

function App() {
  const screen = useAppStore((s) => s.screen);

  return (
    <>
      <IdleTimer />
      {screen === 'home' && <HomeScreen />}
      {screen === 'loading' && <LoadingScreen />}
      {screen === 'results' && <ResultsScreen />}
      {screen === 'map' && <MapScreen />}
    </>
  );
}

export default App;
