import {
  ShaderGradient,
  ShaderGradientCanvas
} from "shadergradient";

export default function BackgroundShader() {
  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: -1
      }}
    >
      <ShaderGradientCanvas
        style={{
          width: "100%",
          height: "100%"
        }}
        fov={120}
        pixelDensity={1}
        pointerEvents="none"
      >
        <ShaderGradient
          animate="on"
          type="waterPlane"
          shader="defaults"

          /* 🔑 Geometry scale */
          scale={10}

          /* Shader motion */
          uTime={8}
          uSpeed={0.002}
          uStrength={0.7}
          uDensity={1.5}

          /* Orientation */
          rotationX={0}
          rotationY={0}
          rotationZ={0}

          /* Colors */
          color1="#000000"
          color2="#2c047b"
          color3="#1f0122"

          reflection={0.15}

          /* Camera */
          cAzimuthAngle={180}
          cPolarAngle={90}
          cDistance={0.9}
          cameraZoom={10}

          /* Lighting */
          lightType="3d"
          brightness={1}
          envPreset="city"
          grain="off"
        />
      </ShaderGradientCanvas>
    </div>
  );
}
