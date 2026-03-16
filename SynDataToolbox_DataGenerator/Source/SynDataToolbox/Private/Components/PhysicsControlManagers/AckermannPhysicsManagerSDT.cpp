#include "Components/PhysicsControlManagers/AckermannPhysicsManagerSDT.h"
#include <math.h>

UAckermannPhysicsManagerSDT::UAckermannPhysicsManagerSDT()
{
}

const FString UAckermannPhysicsManagerSDT::GetPhysicsManagerName() const
{
	return FString("ACKERMANN PHYSICS MANAGER");
}

void UAckermannPhysicsManagerSDT::GetActorReference(AActor* Agent, FHitResult* ActorHit)
{
	AgentToManage = Agent;
	HitHandler = ActorHit;

	//SET ROTATION AND LOCATION
	CurrentPosition = AgentToManage->GetActorLocation();
	OldPosition = CurrentPosition;

	CurrentRotation = AgentToManage->GetActorRotation();
	CurrentRotation.Normalize();
	OldRotation = CurrentRotation;
}

bool UAckermannPhysicsManagerSDT::Reset()
{
	//Restore Original Values
	CurrentPosition = AgentToManage->GetActorLocation();
	OldPosition = CurrentPosition;
	CurrentRotation = AgentToManage->GetActorRotation();
	OldRotation = CurrentRotation;
	return true;
}

void UAckermannPhysicsManagerSDT::SetPhysicsSettings(TArray<float> Settings)
{
	// current order: 
	// AgentMass,	AgentLength, AgentWidth, 
	// FrictionParameter, AngularFrictionParameter
	// MAX_FORCE, MAX_MOMENTUM, MIN_FORCE, MIN_MOMENTUM

	if (Settings.Num() == 10)
	{
		AgentMass = Settings[0];
		AgentLength = Settings[1];
		AgentWidth = Settings[2];
		FrictionParameter = Settings[3];
		AngularFrictionParameter = Settings[4];
		MAX_FORCE = Settings[5];
		MAX_MOMENTUM = Settings[6];
		MIN_FORCE = Settings[7];
		MIN_MOMENTUM = Settings[8];
		isAngleRot = Settings[9];
	}
}

void UAckermannPhysicsManagerSDT::SetNewPosition(TArray<float> Velocities, float DeltaTime, float IsRotAngle)
{
	OldPosition = AgentToManage->GetActorLocation();  // old center position
	OldRotation = AgentToManage->GetActorRotation();  // old center rotation
	UE_LOG(LogTemp, Warning, TEXT("OldRotation: %s"), *OldRotation.ToString());
	UE_LOG(LogTemp, Warning, TEXT("AgentLength: %f"), AgentLength);

	if (IsRotAngle != 0.0)
	{
		RotationAngle = Velocities[1];

	}
	else
	{
		RotationAngle = atan(AgentLength * (Velocities[1] * 180 / PI) / Velocities[0]);  // approximation of the rotation angle (delta)
	}

	OldPosition[0] = OldPosition[0] + ((AgentLength / 2) * cos(OldRotation.Yaw * PI / 180.0));  // old front position
	OldPosition[1] = OldPosition[1] + ((AgentLength / 2) * sin(OldRotation.Yaw * PI / 180.0));  // old front position

	CurrentPosition[0] = (OldPosition[0] + Velocities[0] * cos(RotationAngle + OldRotation.Yaw * PI / 180.0) * DeltaTime);  // update front position
	CurrentPosition[1] = (OldPosition[1] + Velocities[0] * sin(RotationAngle + OldRotation.Yaw * PI / 180.0) * DeltaTime);  // update front position

	CurrentPosition[0] = CurrentPosition[0] - ((AgentLength / 2) * cos(OldRotation.Yaw * PI / 180.0));  // update center position
	CurrentPosition[1] = CurrentPosition[1] - ((AgentLength / 2) * sin(OldRotation.Yaw * PI / 180.0));  // update center position

	CurrentRotation.Yaw = OldRotation.Yaw + (Velocities[0] / AgentLength) * sin(RotationAngle) * DeltaTime;  // update center rotation

	UE_LOG(LogTemp, Warning, TEXT("LinearVelocity: %f"), Velocities[0]);
	UE_LOG(LogTemp, Warning, TEXT("RotationAngle: %f"), RotationAngle);

	UE_LOG(LogTemp, Warning, TEXT("T coord: %s"), *CurrentPosition.ToString());
	UE_LOG(LogTemp, Warning, TEXT("R coord: %s"), *CurrentRotation.ToString());


	// update of the agent position
	AgentToManage->SetActorLocationAndRotation(CurrentPosition, CurrentRotation, true, HitHandler);
}
