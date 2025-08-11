import { BackgroundBeams } from "../components/ui/background-beams";
import Navbar from "../components/navbar/Navbar";
import Hero from "../components/landing/Hero";

const LandingPage = () => {
  return (
    <main>
      <Navbar />
      <Hero />
      <BackgroundBeams />
    </main>
  );
};

export default LandingPage;
