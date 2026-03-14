#include "Components/ActionManagers/LightControlActionManagerSDT.h"
#include "EngineUtils.h"
#include "Engine/World.h"

ALightControlActionManagerSDT::ALightControlActionManagerSDT()
{
    PrimaryActorTick.bCanEverTick = false;
    ActorHit = new FHitResult();
    LightComponent = nullptr;
}

void ALightControlActionManagerSDT::BeginPlay()
{
    Super::BeginPlay();
    FindTargetLight();
}

void ALightControlActionManagerSDT::FindTargetLight()
{
    UE_LOG(LogTemp, Warning, TEXT("🔍 LightControl: Searching for CoordinateActionManagerSDT to find attached SpotLight..."));

    // Iteriamo per trovare il CoordinateActionManagerSDT
    for (TActorIterator<ACoordinateActionManagerSDT> It(GetWorld()); It; ++It)
    {
        ACoordinateActionManagerSDT* CoordManager = *It;
        if (CoordManager && CoordManager->SpotLightComponent)
        {
            // ABBIAMO TROVATO LA LUCE SOLIDALE!
            LightComponent = CoordManager->SpotLightComponent;
            UE_LOG(LogTemp, Warning, TEXT("✅ SUCCESSO: Trovato SpotLightComponent dentro %s"), *CoordManager->GetName());

            // Log parametri iniziali per debug
            UE_LOG(LogTemp, Log, TEXT("   Inner: %.2f | Outer: %.2f | Intensity: %.2f"),
                LightComponent->InnerConeAngle, LightComponent->OuterConeAngle, LightComponent->Intensity);
            return;
        }
    }

    UE_LOG(LogTemp, Error, TEXT("❌ ERRORE: Nessun CoordinateActionManagerSDT con SpotLightComponent trovato nella scena!"));
}

const FString ALightControlActionManagerSDT::GetActionManagerName() const
{
    return "LightControlActionManager(" + GetActorLabel() + ")";
}

const FString ALightControlActionManagerSDT::GetActionManagerSetup() const
{
    // Rimuoviamo SETDIRECTION dalla stringa setup se non lo usiamo più, o lasciamolo per compatibilità.
    // Dato che la luce è solidale, la direzione è controllata dalla camera (Pitch/Yaw del CoordinateManager).
    // Tuttavia, potremmo voler ruotare la luce *rispetto* alla camera.
    return FString("SETCOLOR,SETINTENSITY,SETRADIUS,SETDIRECTION,SETINNERCONE,SETOUTERCONE,SETALL@{}");
}

const int ALightControlActionManagerSDT::ActionToID(const FString& Action) const
{
    if (Action == "SETCOLOR") return SETCOLOR;
    else if (Action == "SETINTENSITY") return SETINTENSITY;
    else if (Action == "SETRADIUS") return SETRADIUS;
    else if (Action == "SETDIRECTION") return SETDIRECTION;
    else if (Action == "SETINNERCONE") return SETINNERCONE;
    else if (Action == "SETOUTERCONE") return SETOUTERCONE;
    else if (Action == "SETALL") return SETALL;
    else return UNKNOWN;
}

const bool ALightControlActionManagerSDT::InitSettings(const TArray<FString>& Settings)
{
    return (Settings.Num() == 0);
}

const int8_t ALightControlActionManagerSDT::PerformAction(TArray<FString>& ActionAndParameters)
{
    if (!LightComponent)
    {
        // Riprova a cercarla se è null (caso di spawn ritardato)
        FindTargetLight();
        if (!LightComponent)
        {
            UE_LOG(LogTemp, Error, TEXT("❌ LightComponent is NULL! Cannot perform action."));
            return -1;
        }
    }

    if (ActionAndParameters.Num() < 1) return -1;

    FString ActionName = ActionAndParameters[0];
    ActionAndParameters.RemoveAt(0);
    const int ActionID = ActionToID(ActionName);

    switch (ActionID)
    {
    case SETCOLOR:      return SetLightColor(ActionAndParameters);
    case SETINTENSITY:  return SetLightIntensity(ActionAndParameters);
    case SETRADIUS:     return SetLightRadius(ActionAndParameters);

    case SETDIRECTION:
        // OPZIONALE: Se vuoi ruotare la luce RELATIVAMENTE alla camera
        // Esempio: la camera guarda dritta, ma la luce punta un po' in alto.
        // Se non ti serve, puoi ritornare 0 e ignorare, o implementare SetRelativeRotation.
        // Qui sotto assumo che tu voglia ignorarlo o implementarlo come rotazione relativa.
        return 0;

    case SETINNERCONE:  return SetInnerConeAngle(ActionAndParameters);
    case SETOUTERCONE:  return SetOuterConeAngle(ActionAndParameters);
    case SETALL:        return SetAllLightParameters(ActionAndParameters);
    default:
        UE_LOG(LogTemp, Error, TEXT("❌ Unknown action: %s"), *ActionName);
        return -1;
    }
}

// --- IMPLEMENTAZIONI PARAMETRI (Invariate nella logica, usano LightComponent) ---

const int8_t ALightControlActionManagerSDT::SetLightColor(TArray<FString>& Parameters)
{
    if (Parameters.Num() != 3) return -1;
    const float R = FCString::Atof(*Parameters[0]);
    const float G = FCString::Atof(*Parameters[1]);
    const float B = FCString::Atof(*Parameters[2]);
    LightComponent->SetLightColor(FLinearColor(R / 255.0f, G / 255.0f, B / 255.0f, 1.0f));
    return 0;
}

const int8_t ALightControlActionManagerSDT::SetLightIntensity(TArray<FString>& Parameters)
{
    if (Parameters.Num() != 1) return -1;
    LightComponent->SetIntensity(FCString::Atof(*Parameters[0]));
    return 0;
}

const int8_t ALightControlActionManagerSDT::SetLightRadius(TArray<FString>& Parameters)
{
    if (Parameters.Num() != 1) return -1;
    LightComponent->SetAttenuationRadius(FCString::Atof(*Parameters[0]));
    return 0;
}

const int8_t ALightControlActionManagerSDT::SetInnerConeAngle(TArray<FString>& Parameters)
{
    if (Parameters.Num() != 1) return -1;
    // Clamp tra 0 e OuterConeAngle attuale
    float NewAngle = FMath::Clamp(FCString::Atof(*Parameters[0]), 0.0f, LightComponent->OuterConeAngle);
    LightComponent->SetInnerConeAngle(NewAngle);
    return 0;
}

const int8_t ALightControlActionManagerSDT::SetOuterConeAngle(TArray<FString>& Parameters)
{
    if (Parameters.Num() != 1) return -1;
    // Clamp tra InnerConeAngle attuale e 89.0f
    float NewAngle = FMath::Clamp(FCString::Atof(*Parameters[0]), LightComponent->InnerConeAngle, 89.0f);
    LightComponent->SetOuterConeAngle(NewAngle);
    return 0;
}

const int8_t ALightControlActionManagerSDT::SetAllLightParameters(TArray<FString>& Parameters)
{
    // R, G, B, Intensity, Radius
    if (Parameters.Num() != 5) return -1;

    const float R = FCString::Atof(*Parameters[0]);
    const float G = FCString::Atof(*Parameters[1]);
    const float B = FCString::Atof(*Parameters[2]);
    const float Intensity = FCString::Atof(*Parameters[3]);
    const float Radius = FCString::Atof(*Parameters[4]);

    LightComponent->SetLightColor(FLinearColor(R / 255.0f, G / 255.0f, B / 255.0f, 1.0f));
    LightComponent->SetIntensity(Intensity);
    LightComponent->SetAttenuationRadius(Radius);

    return 0;
}

// ... (Possess/UnPossess vuoti o standard) ...
void ALightControlActionManagerSDT::Possess() {}
void ALightControlActionManagerSDT::UnPossess() {}
FHitResult* ALightControlActionManagerSDT::GetHitHandler() { return ActorHit; }
void ALightControlActionManagerSDT::Tick(float DeltaTime) { Super::Tick(DeltaTime); }