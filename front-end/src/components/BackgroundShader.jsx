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
          scale={3}

          /* Shader motion */
          uTime={8}
          uSpeed={0.01}
          uStrength={1.5}
          uDensity={1.5}

          /* Orientation */
          rotationX={0}
          rotationY={0}
          rotationZ={0}

          /* Colors */
          color1="#242880"
          color2="#8d7dca"
          color3="#212121"

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
          grain="on"
        />
      </ShaderGradientCanvas>
    </div>
  );
}
