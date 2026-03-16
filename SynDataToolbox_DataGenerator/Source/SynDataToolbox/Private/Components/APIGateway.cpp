// ============================================================================
// APIGateway.cpp - Robust FetchSDTObjects + safe BeginPlay (prevents CDO/null crashes)
// ============================================================================

#include "Components/APIGateway.h"

#include "EngineUtils.h"
#include "DrawDebugHelpers.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"

// SDT classes / interfaces
#include "Components/ActionManagers/ExclusionZoneSDT.h"
#include "Components/Sensors/SensorSDT.h"
#include "Components/ActionManagers/ActionManagerSDT.h"
#include "Components/ResetManagers/ResetManagerSDT.h"

// Sets default values
AAPIGateway::AAPIGateway()
{
	// Set this actor to call Tick() every frame. You can turn this off to improve performance if you don't need it.
	PrimaryActorTick.bCanEverTick = false;
	HeroSocket = MakeShared<UnrealSocketSDT>();
	Mesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Mesh"));
	SetRootComponent(Mesh);
}

// Called when the game starts or when spawned
void AAPIGateway::BeginPlay()
{
	Super::BeginPlay();
	//because ActorHero now can manipulate only "object" spawned into level.
	FetchSDTObjects();
	gameViewport = GEngine->GameViewport;
	gameViewport->bDisableWorldRendering = 1 - showRender;
	FTimerHandle FPSTimerHandle;
	GetWorld()->GetTimerManager().SetTimer(FPSTimerHandle, this, &AAPIGateway::ShowFrameRateOnScreen, 1.0f, true);
	CreateConnection();
}

const int AAPIGateway::CommandToID(const FString& command) const
{
	if (command == "CHANGE") return CHANGE;
	else if (command == "OBS") return OBS;
	else if (command == "CLOSE") return CLOSE;
	else if (command == "SENSORS") return SENSORS;
	else if (command == "RENDER") return RENDER;
	else if (command == "ACTIONS") return ACTIONS;
	else if (command == "SETACTIONMAN") return SETACTIONMAN;
	else if (command == "ACTION") return ACTION;
	else if (command == "RESETS") return RESETS;
	else if (command == "SETRESETMAN") return SETRESETMAN;
	else if (command == "RESET") return RESET;
	else if (command == "FPS") return FPS;
	else if (command == "POI") return POI;
	else if (command == "EXCLUSIONS") return EXCLUSIONS;
	else if (command == "ACPOS") return ACPOS; // ✅ NUOVO COMANDO
	else return UNKNOWN;
}

void AAPIGateway::ShowFrameRateOnScreen()
{
	if (ShowFPS)
	{
		GEngine->AddOnScreenDebugMessage(0, 1.0f, FColor::Yellow, "FPS_" + GetName() + ": " + FString::FromInt(FPSCounter));
	}
	FPSCounter = 0;
}

// Called every frame
void AAPIGateway::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);
}

// Called every frame
void AAPIGateway::RepeatingFunction()
{
	const FString PythonCommand = HeroSocket->TCPSocketListener();
	if (PythonCommand != "")
	{
		FPSCounter++;
		ParseCommand(PythonCommand);
	}
}

void AAPIGateway::CreateConnection()
{
	if (HeroSocket->StartTCPReceiver(port))
	{
		//Start the Listener //thread this eventually
		GetWorldTimerManager().SetTimer(TimerTCPConnectionListener, this, &AAPIGateway::TCPConnectionListener, 0.01, true);
	}
}

void AAPIGateway::TCPConnectionListener()
{
	if (HeroSocket->TCPConnectionListener())
	{

		//can thread this too
		GetWorldTimerManager().SetTimer(TimerRepeatingFunction, this, &AAPIGateway::RepeatingFunction, 0.01, true);
	}
}

const bool AAPIGateway::CloseConnection()
{
	HeroSocket->CloseConnectionSocket();
	UE_LOG(LogTemp, Warning, TEXT("Connection closed on port: %i"), port);
	return true;
}

const bool AAPIGateway::SendSensorsList()
{
	//sends a list of just istanciated sensors
	FString SensorNameList = "";
	for (auto Sensor : SensorsList)
	{
		const FString SensorName = Sensor->GetSensorName();
		SensorNameList += SensorName;
		SensorNameList += "#" + FString::FromInt(Sensor->GetObservationSize()) + "@" + Sensor->GetSensorSetup() + " ";
	}
	const int32 StringLength = SensorNameList.Len();
	HeroSocket->SendBytes(TCHAR_TO_ANSI(*SensorNameList), StringLength);

	return true;
}

const bool AAPIGateway::SendActionManagersList()
{
	FString ActionManagersNameList = "";

	for (IActionManagerSDT* ActionManager : ActionManagersList)
	{
		const FString ActionManagerName = ActionManager->GetActionManagerName();
		ActionManagersNameList += ActionManagerName;
		ActionManagersNameList += "#" + ActionManager->GetActionManagerSetup() + " ";
	}
	const int32 StringLength = ActionManagersNameList.Len();
	HeroSocket->SendBytes(TCHAR_TO_ANSI(*ActionManagersNameList), StringLength);

	return true;
}

const bool AAPIGateway::SendResetManagersList()
{
	FString ResetManagersNameList = "";

	for (IResetManagerSDT* ResetManager : ResetManagersList)
	{
		const FString ResetManagerName = ResetManager->GetResetManagerName();
		ResetManagersNameList += ResetManagerName;
		ResetManagersNameList += " ";
	}
	const int32 StringLength = ResetManagersNameList.Len();

	HeroSocket->SendBytes(TCHAR_TO_ANSI(*ResetManagersNameList), StringLength);

	return true;
}


const bool AAPIGateway::SetCurrentResetManager(TArray<FString>& FieldArray)
{
	bool bSetCurrentResetManagerSuccessful = false;

	const FString ResetManagerName = FieldArray[0];
	FieldArray.RemoveAt(0);
	for (auto ResetManager : ResetManagersList)
	{
		if (ResetManager->IsResetManagerName(ResetManagerName))
		{
			CurrentResetManager = ResetManager;
			bSetCurrentResetManagerSuccessful = CurrentResetManager->ChangeResetSettings(FieldArray);
			break;
		}
	}

	return bSetCurrentResetManagerSuccessful;
}

// =================================================================
// ✅ IMPLEMENTAZIONE CORRETTA: SendExclusionZonesList
// =================================================================

const bool AAPIGateway::SendExclusionZonesList()
{
	FString ZoneData = "";
	int32 ValidZones = 0;

	// Raccogli zone valide
	for (AExclusionZoneSDT* ExclusionZone : ExclusionZonesList)
	{
		if (ExclusionZone && ExclusionZone->IsZoneValid())
		{
			const FString ZoneParams = ExclusionZone->GetZoneParameters();
			if (!ZoneParams.IsEmpty())
			{
				ZoneData += ZoneParams + TEXT(";");
				ValidZones++;
			}
		}
	}

	// ✅ Costruisci risposta con wrapper ZONES_START/ZONES_END
	FString Response;
	if (ValidZones == 0)
	{
		Response = TEXT("ZONES_START::ZONES_END");
		UE_LOG(LogTemp, Warning, TEXT("⚠️ AAPIGateway: Nessuna Exclusion Zone valida da inviare."));
	}
	else
	{
		// Rimuovi ultimo punto e virgola
		ZoneData.RemoveFromEnd(TEXT(";"));
		Response = FString::Printf(TEXT("ZONES_START:%s:ZONES_END"), *ZoneData);
		UE_LOG(LogTemp, Warning, TEXT("📤 AAPIGateway: Inviate %d Exclusion Zone"), ValidZones);
	}

	// Invia tramite socket
	const int32 StringLength = Response.Len();
	HeroSocket->SendBytes(TCHAR_TO_ANSI(*Response), StringLength);

	UE_LOG(LogTemp, Log, TEXT("   Lunghezza messaggio: %d byte"), StringLength);

	return true;
}

// =================================================================
// ✅ NUOVO METODO: SendCurrentActionManagerPosition (ACPOS)
// =================================================================
const bool AAPIGateway::SendCurrentActionManagerPosition()
{
	// Se non c'è un manager selezionato esplicitamente, proviamo a usare il primo disponibile
	if (!CurrentActionManager && ActionManagersList.Num() > 0)
	{
		CurrentActionManager = ActionManagersList[0];
	}

	if (!CurrentActionManager)
	{
		FString ErrorMsg = "ERROR:NoManager";
		HeroSocket->SendBytes(TCHAR_TO_ANSI(*ErrorMsg), ErrorMsg.Len());
		UE_LOG(LogTemp, Error, TEXT("ACPOS: Nessun Action Manager attivo trovato."));
		return false;
	}

	// Cast dell'interfaccia ad AActor per ottenere la trasformazione
	AActor* Actor = Cast<AActor>(CurrentActionManager);
	if (Actor)
	{
		FVector Loc = Actor->GetActorLocation();
		FRotator Rot = Actor->GetActorRotation();

		// Formato: X,Y,Z,Pitch,Yaw,Roll
		FString PosString = FString::Printf(TEXT("%.2f,%.2f,%.2f,%.2f,%.2f,%.2f"),
			Loc.X, Loc.Y, Loc.Z, Rot.Pitch, Rot.Yaw, Rot.Roll);

		HeroSocket->SendBytes(TCHAR_TO_ANSI(*PosString), PosString.Len());
		return true;
	}

	FString ErrorMsg = "ERROR:InvalidActor";
	HeroSocket->SendBytes(TCHAR_TO_ANSI(*ErrorMsg), ErrorMsg.Len());
	return false;
}

const bool AAPIGateway::ChangeSensorsSettings(TArray<FString>& FieldArray) const
{
	bool bChangeSensorsSettingsSuccessful = false;

	const FString SensorName = FieldArray[0];
	FString new_buf = "";
	FieldArray.RemoveAt(0);
	for (auto Sensor : SensorsList)
	{
		if (Sensor->IsSensorName(SensorName))
		{
			bChangeSensorsSettingsSuccessful = Sensor->ChangeSensorSettings(FieldArray);
			if (bChangeSensorsSettingsSuccessful) {
				new_buf = "";
				new_buf = FString::FromInt(Sensor->GetObservationSize());
				int32 StringLength = new_buf.Len();
				HeroSocket->SendBytes(TCHAR_TO_ANSI(*new_buf), StringLength);
			}
			break;
		}
	}
	return bChangeSensorsSettingsSuccessful;
}

const bool AAPIGateway::GetSensorsObs(TArray<FString>& FieldArray)
{
	bool bGetSensorsObsSuccessful = false;

	const FString SensorName = FieldArray[0];
	FieldArray.RemoveAt(0);
	for (auto Sensor : SensorsList)
	{
		if (Sensor->IsSensorName(SensorName))
		{
			const uint32 size = Sensor->GetObservationSize();
			uint8* const Buffer = new uint8[size];
			bGetSensorsObsSuccessful = Sensor->GetLastObs(Buffer);
			if (bGetSensorsObsSuccessful)
			{
				HeroSocket->SendObsBytes(Buffer, size);
			}
			delete[] Buffer;
			break;
		}
	}

	return bGetSensorsObsSuccessful;
}

const bool AAPIGateway::PerformAction(TArray<FString>& FieldArray)
{
	bool bPerformActionSuccessful = true;
	bool bHit = false;

	const FString ActionManagerName = FieldArray[0];
	FieldArray.RemoveAt(0);
	FString Command = FieldArray[0];
	for (auto ActionManager : ActionManagersList) {
		if (ActionManager->IsActionManagerName(ActionManagerName))
		{
			TArray<FString> Action;
			Command.ParseIntoArray(Action, TEXT(";"), true);
			const int8_t PerformActionCode = ActionManager->PerformAction(Action);
			if (PerformActionCode == -1)
			{
				bPerformActionSuccessful = false;
			}
			if (bPerformActionSuccessful)
			{
				if (PerformActionCode != 0)
				{
					bHit = true;
				}
			}
			HeroSocket->SendBytes(&bHit, 1);
			break;
		}
	}
	return bPerformActionSuccessful;
}

const bool AAPIGateway::PerformReset(TArray<FString>& FieldArray)
{
	const FString ResetManagerName = FieldArray[0];
	FieldArray.Empty();
	bool ResetResult = true;

	//TODO: Iterate over ResetManagerList
	for (auto ResetManager : ResetManagersList) {
		if (ResetManager->GetResetManagerName().Equals(ResetManagerName)) {
			ResetResult = ResetManager->PerformReset(FieldArray);
			HeroSocket->SendBytes(&ResetResult, 1);
			break;
		}
	}
	return ResetResult;
}

// =================================================================
// IMPLEMENTAZIONE NUOVE FUNZIONI PER GESTIONE POI (Point of Interest)
// =================================================================

const FVector AAPIGateway::FindTargetPointLocation() const
{
	const FName PoITag(TEXT("TargetPointPoI"));

	for (TActorIterator<AActor> Itr(GetWorld()); Itr; ++Itr)
	{
		if (Itr->ActorHasTag(PoITag))
		{
			UE_LOG(LogTemp, Warning, TEXT("AAPIGateway: TargetPointPoI trovato a %s"), *Itr->GetActorLocation().ToString());
			return Itr->GetActorLocation();
		}
	}

	UE_LOG(LogTemp, Error, TEXT("AAPIGateway: ATTENZIONE: TargetPointPoI con tag 'TargetPointPoI' non trovato. Restituisco [0.0, 0.0, 0.0]."));
	return FVector::ZeroVector;
}

const bool AAPIGateway::SendPoICoordinates()
{
	FVector PoILoc = FindTargetPointLocation();
	const int PoICode = POI;

	FString PoIString = FString::Printf(TEXT("%d %f %f %f"),
		PoICode, PoILoc.X, PoILoc.Y, PoILoc.Z);

	const int32 StringLength = PoIString.Len();
	HeroSocket->SendBytes(TCHAR_TO_ANSI(*PoIString), StringLength);

	UE_LOG(LogTemp, Warning, TEXT("AAPIGateway: Inviato PoI: %s"), *PoIString);

	return true;
}

// =================================================================

void AAPIGateway::ParseCommand(const FString PythonCommand)
{
	TArray<FString> CommandArray;
	PythonCommand.ParseIntoArray(CommandArray, TEXT(" "), true);

	for (auto Command = CommandArray.CreateConstIterator(); Command; ++Command)
	{
		TArray<FString> FieldArray;
		Command->ParseIntoArray(FieldArray, TEXT("_"), true);

		const FString CommandName = FieldArray[0];
		FieldArray.RemoveAt(0);
		const int FieldID = CommandToID(CommandName);

		bool bValidCommand = false;

		switch (FieldID)
		{
		case SENSORS:
		{
			bValidCommand = SendSensorsList();
			if (!bValidCommand) UE_LOG(LogTemp, Error, TEXT("SENSORS"));
		} break;
		case ACTIONS:
		{
			bValidCommand = SendActionManagersList();
			if (!bValidCommand) UE_LOG(LogTemp, Error, TEXT("ACTIONS"));
		} break;
		case RESETS:
		{
			bValidCommand = SendResetManagersList();
			if (!bValidCommand) UE_LOG(LogTemp, Error, TEXT("RESETS"));
		} break;
		case SETRESETMAN:
		{
			bValidCommand = SetCurrentResetManager(FieldArray);
			if (!bValidCommand) UE_LOG(LogTemp, Error, TEXT("SETRESETMAN"));
		} break;
		case CHANGE:
		{
			bValidCommand = ChangeSensorsSettings(FieldArray);
			if (!bValidCommand) UE_LOG(LogTemp, Error, TEXT("CHANGE"));
		} break;
		case OBS:
		{
			bValidCommand = GetSensorsObs(FieldArray);
			if (!bValidCommand) UE_LOG(LogTemp, Error, TEXT("OBS"));
		} break;
		case ACTION:
		{
			bValidCommand = PerformAction(FieldArray);
			if (!bValidCommand) UE_LOG(LogTemp, Error, TEXT("ACTION"));
		} break;
		case RESET:
		{
			bValidCommand = PerformReset(FieldArray);
			if (!bValidCommand) UE_LOG(LogTemp, Error, TEXT("RESET"));
		} break;
		case RENDER:
		{
			gameViewport->bDisableWorldRendering = 0;
			bValidCommand = true;
		} break;
		case FPS:
		{
			ShowFPS = true;
			bValidCommand = true;
		} break;
		case POI:
		{
			bValidCommand = SendPoICoordinates();
			if (!bValidCommand) UE_LOG(LogTemp, Error, TEXT("POI - Fallito l'invio delle coordinate."));
		} break;
		case EXCLUSIONS:
		{
			bValidCommand = SendExclusionZonesList();
			if (!bValidCommand) UE_LOG(LogTemp, Error, TEXT("EXCLUSIONS - Fallito l'invio delle zone."));
		} break;
		case ACPOS:
		{
			bValidCommand = SendCurrentActionManagerPosition();
			if (!bValidCommand) UE_LOG(LogTemp, Error, TEXT("ACPOS - Fallito recupero posizione"));
		} break;
		case CLOSE:
		{
			bValidCommand = CloseConnection();
			if (!bValidCommand) UE_LOG(LogTemp, Error, TEXT("CLOSE"));
		} break;
		default:
		{
			UE_LOG(LogTemp, Error, TEXT("Unknown command: %s"), *CommandName);
		} break;
		}
		if (!bValidCommand)
		{
			UE_LOG(LogTemp, Error, TEXT("CLOSED"));
			CloseConnection();
			return;
		}
	}
}

void AAPIGateway::FetchSDTObjects()
{
	UE_LOG(LogTemp, Warning, TEXT("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"));
	UE_LOG(LogTemp, Warning, TEXT("🔍 INIZIO SCANSIONE OGGETTI SDT"));
	UE_LOG(LogTemp, Warning, TEXT("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"));

	int32 SensorsFound = 0;
	int32 ActionManagersFound = 0;
	int32 ResetManagersFound = 0;
	int32 ExclusionZonesFound = 0;
	int32 ExclusionZonesInvalid = 0;
	int32 UnknownSDTFound = 0;

	UWorld* World = GetWorld();
	if (!World)
	{
		UE_LOG(LogTemp, Error, TEXT("❌ ERRORE CRITICO: GetWorld() è nullptr!"));
		return;
	}

	UE_LOG(LogTemp, Log, TEXT("✅ World valido, inizio iterazione attori...\n"));

	int32 ActorIndex = 0;
	int32 CDOsSkipped = 0;
	int32 InvalidActorsSkipped = 0;

	for (TActorIterator<AActor> ActorItr(World); ActorItr; ++ActorItr)
	{
		ActorIndex++;
		AActor* Actor = *ActorItr;

		// Skip null / CDO / Archetype / Template Actors
		if (!Actor ||
			Actor->HasAnyFlags(RF_ClassDefaultObject | RF_ArchetypeObject) ||
			Actor->IsTemplate())
		{
			CDOsSkipped++;
			continue;
		}

		if (!::IsValid(Actor) || Actor->IsActorBeingDestroyed())
		{
			InvalidActorsSkipped++;
			continue;
		}

		const FString ActorName = Actor->GetName();

		if (!ActorName.Contains(TEXT("SDT")))
		{
			continue;
		}
		if (ActorName.Equals(GetName()))
		{
			UE_LOG(LogTemp, Verbose, TEXT("[%d] Skip: APIGateway stesso"), ActorIndex);
			continue;
		}

		UE_LOG(LogTemp, Verbose, TEXT("[%d] Analisi: %s"), ActorIndex, *ActorName);

		// ExclusionZoneSDT
		UClass* ActorClass = Actor->GetClass();
		if (ActorClass && ActorClass->IsChildOf(AExclusionZoneSDT::StaticClass()))
		{
			UE_LOG(LogTemp, Log, TEXT("   🔍 ExclusionZoneSDT trovato: %s"), *ActorName);

			AExclusionZoneSDT* ZoneActor = Cast<AExclusionZoneSDT>(Actor);
			if (!::IsValid(ZoneActor))
			{
				UE_LOG(LogTemp, Error, TEXT("      ❌ Cast fallito o zona non valida"));
				ExclusionZonesInvalid++;
				continue;
			}

			if (!ZoneActor->ExclusionBox || !::IsValid(ZoneActor->ExclusionBox))
			{
				UE_LOG(LogTemp, Error, TEXT("      ❌ ExclusionBox è nullptr o non valido"));
				ExclusionZonesInvalid++;
				continue;
			}

			if (!ZoneActor->IsZoneValid())
			{
				UE_LOG(LogTemp, Warning, TEXT("      ⚠️ Zona non completamente inizializzata o invalida"));
				ExclusionZonesInvalid++;
				continue;
			}

			ExclusionZonesFound++;
			ExclusionZonesList.Add(ZoneActor);
			UE_LOG(LogTemp, Warning, TEXT("      ✅ Zona VALIDA: %s"), *ActorName);

			const FVector Center = ZoneActor->GetActorLocation();
			const FVector Extent = ZoneActor->ExclusionBox->GetScaledBoxExtent();
			const FVector Size = Extent * 2.0f;

			UE_LOG(LogTemp, Log, TEXT("         Centro: (%.1f, %.1f, %.1f)"),
				Center.X, Center.Y, Center.Z);
			UE_LOG(LogTemp, Log, TEXT("         Dimensioni: (%.1f x %.1f x %.1f) cm"),
				Size.X, Size.Y, Size.Z);

			continue;
		}

		// Cast interfacce
		bool bInterfaceFound = false;
		if (ActorClass && ActorClass->ImplementsInterface(USensorSDT::StaticClass()))
		{
			ISensorSDT* Sensor = Cast<ISensorSDT>(Actor);
			if (Sensor)
			{
				SensorsList.Add(Sensor);
				SensorsFound++;
				UE_LOG(LogTemp, Warning, TEXT("   📷 Sensor: %s"), *Sensor->GetSensorName());
				bInterfaceFound = true;
			}
		}

		if (!bInterfaceFound && ActorClass && ActorClass->ImplementsInterface(UActionManagerSDT::StaticClass()))
		{
			IActionManagerSDT* ActionManager = Cast<IActionManagerSDT>(Actor);
			if (ActionManager)
			{
				ActionManagersList.Add(ActionManager);
				ActionManagersFound++;
				UE_LOG(LogTemp, Warning, TEXT("   🎮 ActionManager: %s"),
					*ActionManager->GetActionManagerName());
				bInterfaceFound = true;
			}
		}

		if (!bInterfaceFound && ActorClass && ActorClass->ImplementsInterface(UResetManagerSDT::StaticClass()))
		{
			IResetManagerSDT* ResetManager = Cast<IResetManagerSDT>(Actor);
			if (ResetManager)
			{
				ResetManagersList.Add(ResetManager);
				ResetManagersFound++;
				UE_LOG(LogTemp, Warning, TEXT("   🔄 ResetManager: %s"),
					*ResetManager->GetResetManagerName());
				bInterfaceFound = true;
			}
		}

		if (!bInterfaceFound)
		{
			UnknownSDTFound++;
			UE_LOG(LogTemp, Verbose, TEXT("   ❓ Oggetto SDT sconosciuto: %s"), *ActorName);
		}
	}

	// Riepilogo
	UE_LOG(LogTemp, Warning, TEXT("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"));
	UE_LOG(LogTemp, Warning, TEXT("📊 RIEPILOGO SCANSIONE"));
	UE_LOG(LogTemp, Warning, TEXT("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"));
	UE_LOG(LogTemp, Warning, TEXT("Attori scansionati:      %d"), ActorIndex);
	UE_LOG(LogTemp, Warning, TEXT("CDO/Template saltati:    %d"), CDOsSkipped);
	UE_LOG(LogTemp, Warning, TEXT("Attori invalidi saltati: %d"), InvalidActorsSkipped);
	UE_LOG(LogTemp, Warning, TEXT(""));
	UE_LOG(LogTemp, Warning, TEXT("📷 Sensors:              %d"), SensorsFound);
	UE_LOG(LogTemp, Warning, TEXT("🎮 Action Managers:      %d"), ActionManagersFound);
	UE_LOG(LogTemp, Warning, TEXT("🔄 Reset Managers:       %d"), ResetManagersFound);
	UE_LOG(LogTemp, Warning, TEXT("✅ Exclusion Zones:      %d"), ExclusionZonesFound);

	if (ExclusionZonesInvalid > 0)
	{
		UE_LOG(LogTemp, Warning, TEXT("❌ Exclusion Zones KO:   %d"), ExclusionZonesInvalid);
	}

	if (UnknownSDTFound > 0)
	{
		UE_LOG(LogTemp, Warning, TEXT("❓ Oggetti sconosciuti:  %d"), UnknownSDTFound);
	}

	UE_LOG(LogTemp, Warning, TEXT("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"));

	// Setup debug action manager
	if (DebugActionManager && ActionManagersList.Num() >= 1)
	{
		APlayerController* PC = World ? World->GetFirstPlayerController() : nullptr;
		AActionManagerController* PlayerManager = PC ? Cast<AActionManagerController>(PC) : nullptr;

		if (PlayerManager)
		{
			PlayerManager->SetupActorListToPossess(ActionManagersList);
			UE_LOG(LogTemp, Warning, TEXT("✅ Debug ActionManager configurato\n"));
		}
		else
		{
			UE_LOG(LogTemp, Warning, TEXT("⚠️ Debug ActionManager NON configurato: PlayerManager nullo"));
		}
	}

	UE_LOG(LogTemp, Warning, TEXT("✅ FetchSDTObjects COMPLETATO\n"));
}